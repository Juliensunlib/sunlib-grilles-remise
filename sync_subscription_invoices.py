"""
Synchronisation automatique des factures d'abonnement Sellsy V2.0
Gestion des remises dynamiques via grilles Airtable
"""

import os
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional
import logging

# Import des clients
from src.airtable_client import AirtableClient
from src.sellsy_client import SellsyClient

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SubscriptionInvoiceSync:
    """Gestionnaire de synchronisation des factures d'abonnement"""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialise le synchroniseur
        
        Args:
            dry_run: Si True, simule sans créer réellement les factures
        """
        self.dry_run = dry_run
        
        # Validation de la configuration
        self._validate_config()
        
        # Initialisation des clients
        self.airtable = AirtableClient(
            api_key=os.getenv('AIRTABLE_API_KEY'),
            base_id=os.getenv('AIRTABLE_BASE_ID'),
            table_services=os.getenv('AIRTABLE_TABLE_NAME', 'service_sellsy'),
            table_grilles=os.getenv('AIRTABLE_TABLE_GRILLES', 'grilles_remise')
        )
        
        # ✅ CORRECTION: Passer les credentials OAuth à SellsyClient
        self.sellsy = SellsyClient(
            consumer_token=os.getenv('SELLSY_CONSUMER_TOKEN'),
            consumer_secret=os.getenv('SELLSY_CONSUMER_SECRET'),
            user_token=os.getenv('SELLSY_USER_TOKEN'),
            user_secret=os.getenv('SELLSY_USER_SECRET')
        )
        
        # Cache pour la grille par défaut
        self._default_grid: Optional[Dict] = None
    
    def _validate_config(self):
        """Valide que toutes les variables d'environnement sont présentes"""
        required_vars = [
            'AIRTABLE_API_KEY',
            'AIRTABLE_BASE_ID',
            'AIRTABLE_TABLE_NAME',
            'SELLSY_CONSUMER_TOKEN',
            'SELLSY_CONSUMER_SECRET',
            'SELLSY_USER_TOKEN',
            'SELLSY_USER_SECRET'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing)}")
        
        logger.info("✅ Configuration validée avec succès")
        logger.info(f"📊 Base Airtable: {os.getenv('AIRTABLE_BASE_ID')[:10]}***")
        logger.info(f"📋 Table services: {os.getenv('AIRTABLE_TABLE_NAME')}")
        logger.info(f"📊 Table grilles: {os.getenv('AIRTABLE_TABLE_GRILLES', 'grilles_remise')}")
    
    def get_default_discount_grid(self) -> Dict:
        """
        Récupère la grille de remise par défaut depuis Airtable
        Utilise un cache pour éviter les appels répétés
        
        Returns:
            Dictionnaire contenant les pourcentages de remise par année
            
        Raises:
            Exception: Si aucune grille par défaut n'est trouvée
        """
        if self._default_grid:
            return self._default_grid
        
        grids = self.airtable.get_discount_grids()
        
        for grid in grids:
            if grid.get('Par défaut', False):
                self._default_grid = grid
                return grid
        
        raise Exception("❌ Aucune grille de remise par défaut n'est définie dans Airtable")
    
    def calculate_discount(self, mois_ecoules: int, grid: Dict) -> float:
        """
        Calcule le pourcentage de remise selon le mois écoulé et la grille
        
        Args:
            mois_ecoules: Nombre de mois écoulés depuis le début
            grid: Grille de remise (dict avec Année 1, 2, 3+)
            
        Returns:
            Pourcentage de remise (0-100)
        """
        if mois_ecoules <= 12:
            return grid.get('Remise année 1', 0)
        elif mois_ecoules <= 24:
            return grid.get('Remise année 2', 0)
        else:
            return grid.get('Remise année 3+', 0)
    
    def process_single_subscription(self, service: Dict) -> bool:
        """
        Traite un abonnement individuel
        
        Args:
            service: Dictionnaire contenant les données du service Airtable
            
        Returns:
            True si la facture a été créée avec succès, False sinon
        """
        try:
            record_id = service['id']
            fields = service['fields']
            
            # Extraction des données
            service_name = fields.get('Nom du service', 'Service')
            client_id = fields.get('ID client Sellsy')
            product_id = fields.get('ID Sellsy')
            prix_ht = fields.get('Prix HT', 0)
            date_debut = fields.get('Date de début')
            mois_factures = fields.get('Mois facturés', 0)
            occurrences_restantes = fields.get('Occurrences restantes', 0)
            
            # Validation des données essentielles
            if not all([client_id, product_id, date_debut, prix_ht > 0]):
                logger.warning(f"⚠️  Données incomplètes pour {service_name}")
                return False
            
            # Calcul des mois écoulés
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
            aujourd_hui = datetime.now()
            mois_ecoules = (aujourd_hui.year - date_debut_obj.year) * 12 + \
                          (aujourd_hui.month - date_debut_obj.month)
            
            logger.info(f"📋 Traitement: {service_name}")
            logger.info("=" * 70)
            logger.info(f"  📅 Date début: {date_debut}, Mois écoulés: {mois_ecoules}, "
                       f"Mois facturés: {mois_factures}, Aujourd'hui: {aujourd_hui.strftime('%Y-%m-%d')}")
            
            # Vérifier si une facturation est due
            if mois_ecoules <= mois_factures:
                logger.info(f"  ⏭️  Pas de facturation due (mois écoulés: {mois_ecoules} ≤ mois facturés: {mois_factures})")
                return False
            
            logger.info(f"  ✅ Facturation du mois {mois_factures + 1}")
            logger.info(f"  🚀 Création de la facture...")
            
            # Récupération de la grille de remise
            grille_id = fields.get('Grille de remise')
            if grille_id and len(grille_id) > 0:
                # Grille spécifique liée
                grille = self.airtable.get_discount_grid(grille_id[0])
                logger.info(f"  📊 Grille spécifique: '{grille.get('Nom', 'N/A')}'")
            else:
                # Grille par défaut
                grille = self.get_default_discount_grid()
                logger.info(f"  📊 Grille par défaut: '{grille.get('Nom', 'N/A')}'")
            
            # Calcul de la remise
            appliquer_remise = fields.get('Appliquer remise dégressive', True)
            if appliquer_remise:
                remise_pct = self.calculate_discount(mois_factures + 1, grille)
                montant_remise = round(prix_ht * (remise_pct / 100), 2)
                prix_final = round(prix_ht - montant_remise, 2)
                
                # Construction du libellé de remise
                nom_grille = grille.get('Nom', 'Offre')
                libelle_remise = f"🎉 {nom_grille} (-{int(remise_pct)}%)"
            else:
                remise_pct = 0
                montant_remise = 0
                prix_final = prix_ht
                libelle_remise = ""
            
            logger.info(f"  💰 Prix HT: {prix_ht}€ | Remise: {remise_pct}% | Final: {prix_final}€")
            
            # Mode dry-run : simulation uniquement
            if self.dry_run:
                logger.info(f"  🧪 MODE DRY-RUN: Facture non créée (test uniquement)")
                logger.info(f"     - Client ID: {client_id}")
                logger.info(f"     - Produit ID: {product_id}")
                logger.info(f"     - Montant final: {prix_final}€ HT")
                logger.info(f"     - Remise: {libelle_remise}")
                return True
            
            # Création de la facture dans Sellsy
            logger.info(f"  📤 Envoi de la facture à Sellsy...")
            result = self.sellsy.create_invoice(
                client_id=str(client_id),
                product_id=str(product_id),
                prix_ht=prix_ht,
                remise_pct=remise_pct,
                libelle_remise=libelle_remise,
                service_name=service_name
            )
            
            invoice_id = result.get('invoice_id')
            logger.info(f"  ✅ Facture créée dans Sellsy ! (ID: {invoice_id})")
            
            # Mise à jour des compteurs dans Airtable
            nouveau_mois_factures = mois_factures + 1
            nouvelles_occurrences = max(0, occurrences_restantes - 1)
            
            self.airtable.update_service_counters(
                record_id=record_id,
                mois_factures=nouveau_mois_factures,
                occurrences_restantes=nouvelles_occurrences
            )
            
            logger.info(f"  ✅ Compteurs mis à jour dans Airtable")
            logger.info(f"     - Mois facturés: {mois_factures} → {nouveau_mois_factures}")
            logger.info(f"     - Occurrences restantes: {occurrences_restantes} → {nouvelles_occurrences}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Échec de la création de la facture")
            logger.error(f"  ❌ {str(e)}")
            return False
    
    def run(self):
        """Point d'entrée principal : traite tous les abonnements éligibles"""
        try:
            logger.info("=" * 70)
            logger.info("DÉMARRAGE DE LA SYNCHRONISATION DES FACTURES D'ABONNEMENT V2.0")
            logger.info("=" * 70)
            
            # Récupération des abonnements éligibles
            services = self.airtable.get_eligible_subscriptions()
            
            if not services:
                logger.info("ℹ️  Aucun abonnement éligible à facturer aujourd'hui")
                return
            
            logger.info(f"📊 {len(services)} abonnement(s) éligible(s) trouvé(s)")
            logger.info("")
            
            # Traitement de chaque abonnement
            success_count = 0
            error_count = 0
            
            for service in services:
                try:
                    if self.process_single_subscription(service):
                        success_count += 1
                    logger.info("")  # Ligne vide entre les abonnements
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Erreur: {str(e)}")
                    logger.info("")
            
            # Résumé
            logger.info("=" * 70)
            logger.info("RÉSUMÉ DE LA SYNCHRONISATION")
            logger.info("=" * 70)
            logger.info(f"✅ Succès: {success_count}")
            logger.info(f"❌ Échecs: {error_count}")
            logger.info(f"📊 Total traité: {len(services)}")
            
            if self.dry_run:
                logger.info("🧪 Mode DRY-RUN: Aucune modification réelle effectuée")
            
        except Exception as e:
            logger.error(f"❌ ERREUR CRITIQUE: {str(e)}")
            raise


def main():
    """Point d'entrée du script"""
    # Lecture du mode dry-run depuis les variables d'environnement
    dry_run_env = os.getenv('DRY_RUN', 'false').lower()
    dry_run = dry_run_env in ['true', '1', 'yes']
    
    logger.info(f"🎯 Démarrage de la synchronisation...")
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔧 Mode: {'PRODUCTION' if not dry_run else 'TEST (DRY-RUN)'}")
    logger.info("")
    
    try:
        sync = SubscriptionInvoiceSync(dry_run=dry_run)
        sync.run()
        
        logger.info("")
        logger.info("🎉 Synchronisation terminée avec succès !")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ ERREUR FATALE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
