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
from src.sellsy_client_v2 import SellsyClientV2

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
        
        # ✅ Nouveau client Sellsy v2 avec OAuth2
        self.sellsy = SellsyClientV2(
            client_id=os.getenv('SELLSY_V2_CLIENT_ID'),
            client_secret=os.getenv('SELLSY_V2_CLIENT_SECRET')
        )
        
        # Cache pour la grille par défaut
        self._default_grid: Optional[Dict] = None
    
    def _validate_config(self):
        """Valide que toutes les variables d'environnement sont présentes"""
        required_vars = [
            'AIRTABLE_API_KEY',
            'AIRTABLE_BASE_ID',
            'AIRTABLE_TABLE_NAME',
            'SELLSY_V2_CLIENT_ID',
            'SELLSY_V2_CLIENT_SECRET'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing)}")
        
        logger.info("✅ Configuration validée avec succès")
        logger.info(f"📊 Base Airtable: {os.getenv('AIRTABLE_BASE_ID')[:10]}***")
        logger.info(f"📋 Table services: {os.getenv('AIRTABLE_TABLE_NAME')}")
        logger.info(f"📊 Table grilles: {os.getenv('AIRTABLE_TABLE_GRILLES', 'grilles_remise')}")
        logger.info(f"🔐 Sellsy API: v2 (OAuth2)")
    
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
            if grid.get('Grille par défaut', False):
                self._default_grid = grid
                return grid

        raise Exception("❌ Aucune grille de remise par défaut n'est définie dans Airtable")
    
    def get_discount_info(self, mois_ecoules: int, grid: Dict) -> tuple:
        """
        Récupère le pourcentage de remise et le label selon l'année en cours

        Args:
            mois_ecoules: Nombre de mois écoulés depuis le début
            grid: Grille de remise (dict avec Année 1 (%), Label Année 1, etc.)

        Returns:
            Tuple (pourcentage de remise, label) ou (0, "") si pas de remise
        """
        if mois_ecoules <= 12:
            pct = grid.get('Année 1 (%)', 0)
            label = grid.get('Label Année 1', '')
        elif mois_ecoules <= 24:
            pct = grid.get('Année 2 (%)', 0)
            label = grid.get('Label Année 2', '')
        else:
            pct = grid.get('Année 3+ (%)', 0)
            label = grid.get('Label Année 3+', '')

        # Convertir en float et s'assurer que c'est un nombre valide
        try:
            pct = float(pct) if pct else 0
        except (ValueError, TypeError):
            pct = 0

        # Ne retourner que si le pourcentage est > 0
        if pct > 0 and label:
            return (pct, label)
        else:
            return (0, "")
    
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
            client_id = fields.get('ID_Sellsy_abonné')  # ID du client dans Sellsy
            product_id = fields.get('ID Sellsy')  # ID du produit dans Sellsy
            prix_ht = fields.get('Prix HT', 0)
            date_debut = fields.get('Date de début')
            mois_factures = fields.get('Mois facturés', 0)
            occurrences_restantes = fields.get('Occurrences restantes', 0)
            
            # Validation des données essentielles
            missing_data = []
            if not client_id:
                missing_data.append("ID client (ID_Sellsy_abonné)")
            if not product_id:
                missing_data.append("ID produit (ID Sellsy)")
            if not date_debut:
                missing_data.append("Date de début")
            if not (prix_ht and prix_ht > 0):
                missing_data.append(f"Prix HT valide (actuel: {prix_ht})")
            
            if missing_data:
                logger.warning(f"⚠️  Données incomplètes pour {service_name}")
                logger.warning(f"     Champs manquants: {', '.join(missing_data)}")
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

            # Protection anti-double facturation : ne facturer qu'UN SEUL mois à la fois
            if mois_ecoules > mois_factures + 1:
                logger.warning(f"  ⚠️  RETARD DÉTECTÉ : {mois_ecoules - mois_factures} mois non facturés")
                logger.warning(f"  ⚠️  Pour éviter la double facturation, on facture uniquement le mois {mois_factures + 1}")
                logger.warning(f"  ⚠️  Les mois suivants seront facturés lors des prochaines exécutions")

            logger.info(f"  ✅ Facturation du mois {mois_factures + 1}")
            logger.info(f"  🚀 Création de la facture...")

            # Calcul de la remise (optionnel)
            appliquer_remise = fields.get('Appliquer remise dégressive', True)

            if appliquer_remise:
                # Récupération de la grille de remise uniquement si nécessaire
                try:
                    grille_id = fields.get('Grille de remise')
                    if grille_id and len(grille_id) > 0:
                        # Grille spécifique liée
                        grille = self.airtable.get_discount_grid(grille_id[0])
                        logger.info(f"  📊 Grille spécifique: '{grille.get('Nom de la grille', 'N/A')}'")
                    else:
                        # Grille par défaut
                        grille = self.get_default_discount_grid()
                        logger.info(f"  📊 Grille par défaut: '{grille.get('Nom de la grille', 'N/A')}'")

                    # Récupération du pourcentage et du label pour l'année en cours
                    remise_pct, libelle_remise = self.get_discount_info(mois_factures + 1, grille)
                    montant_remise = round(prix_ht * (remise_pct / 100), 2)
                    prix_final = round(prix_ht - montant_remise, 2)

                except Exception as e:
                    logger.warning(f"  ⚠️  Impossible de récupérer la grille de remise: {str(e)}")
                    logger.warning(f"  ⚠️  Facture créée sans remise")
                    remise_pct = 0
                    montant_remise = 0
                    prix_final = prix_ht
                    libelle_remise = ""
            else:
                logger.info(f"  📊 Remise désactivée pour cet abonnement")
                remise_pct = 0
                montant_remise = 0
                prix_final = prix_ht
                libelle_remise = ""
            
            if remise_pct > 0 and libelle_remise:
                logger.info(f"  💰 Prix HT: {prix_ht}€ | Remise: {remise_pct}% ({libelle_remise}) | Final: {prix_final}€")
            else:
                logger.info(f"  💰 Prix HT: {prix_ht}€ | Pas de remise")
            
            # Mode dry-run : simulation uniquement
            if self.dry_run:
                logger.info(f"  🧪 MODE DRY-RUN: Facture non créée (test uniquement)")
                logger.info(f"     - Client ID: {client_id}")
                logger.info(f"     - Produit ID: {product_id}")
                logger.info(f"     - Montant final: {prix_final}€ HT")
                logger.info(f"     - Remise: {libelle_remise}")
                return True
            
            # Création de la facture dans Sellsy
            logger.info(f"  📤 Envoi de la facture à Sellsy v2...")
            result = self.sellsy.create_invoice(
                client_id=int(client_id),
                product_id=int(product_id),
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
    
    def group_services_by_client_and_date(self, services: List[Dict]) -> Dict[tuple, List[Dict]]:
        """
        Groupe les services par (client_id, date_facturation)

        Args:
            services: Liste des services éligibles

        Returns:
            Dictionnaire avec clé (client_id, date) et valeur liste de services
        """
        from collections import defaultdict
        grouped = defaultdict(list)

        for service in services:
            fields = service['fields']
            client_id = fields.get('ID_Sellsy_abonné')
            date_debut = fields.get('Date de début')
            mois_factures = fields.get('Mois facturés', 0)

            # Calculer la date de facturation (mois suivant)
            if client_id and date_debut:
                date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
                date_facturation = date_debut_obj + relativedelta(months=mois_factures + 1)
                date_key = date_facturation.strftime('%Y-%m')

                key = (str(client_id), date_key)
                grouped[key].append(service)

        return dict(grouped)

    def process_grouped_subscription(self, client_id: str, date_key: str, services: List[Dict]) -> bool:
        """
        Traite un groupe d'abonnements pour un même client et une même date
        Crée une seule facture avec plusieurs lignes

        Args:
            client_id: ID du client Sellsy
            date_key: Clé de date au format YYYY-MM
            services: Liste des services à facturer ensemble

        Returns:
            True si la facture a été créée avec succès, False sinon
        """
        try:
            logger.info(f"📋 Traitement groupé: Client {client_id} - Date {date_key}")
            logger.info("=" * 70)
            logger.info(f"  📦 {len(services)} service(s) à facturer ensemble")

            # Préparation des lignes de facture
            invoice_lines = []
            services_to_update = []

            for service in services:
                record_id = service['id']
                fields = service['fields']

                # Extraction des données
                service_name = fields.get('Nom du service', 'Service')
                product_id = fields.get('ID Sellsy')
                prix_ht = fields.get('Prix HT', 0)
                date_debut = fields.get('Date de début')
                mois_factures = fields.get('Mois facturés', 0)
                occurrences_restantes = fields.get('Occurrences restantes', 0)

                # Validation des données essentielles
                if not product_id or not date_debut or not (prix_ht and prix_ht > 0):
                    logger.warning(f"  ⚠️  Données incomplètes pour {service_name}, ignoré")
                    continue

                # Calcul des mois écoulés
                date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
                aujourd_hui = datetime.now()
                mois_ecoules = (aujourd_hui.year - date_debut_obj.year) * 12 + \
                              (aujourd_hui.month - date_debut_obj.month)

                logger.info(f"  • {service_name}")
                logger.info(f"    📅 Mois écoulés: {mois_ecoules}, Mois facturés: {mois_factures}")

                # Vérifier si une facturation est due
                if mois_ecoules <= mois_factures:
                    logger.info(f"    ⏭️  Pas de facturation due")
                    continue

                if mois_ecoules > mois_factures + 1:
                    logger.warning(f"    ⚠️  RETARD : {mois_ecoules - mois_factures} mois non facturés")
                    logger.warning(f"    ⚠️  Facturation uniquement du mois {mois_factures + 1}")

                logger.info(f"    ✅ Facturation du mois {mois_factures + 1}")

                # Calcul de la remise
                appliquer_remise = fields.get('Appliquer remise dégressive', True)
                remise_pct = 0
                montant_remise = 0
                libelle_remise = ""

                if appliquer_remise:
                    try:
                        grille_id = fields.get('Grille de remise')
                        if grille_id and len(grille_id) > 0:
                            grille = self.airtable.get_discount_grid(grille_id[0])
                            logger.info(f"    📊 Grille: '{grille.get('Nom de la grille', 'N/A')}'")
                        else:
                            grille = self.get_default_discount_grid()
                            logger.info(f"    📊 Grille par défaut: '{grille.get('Nom de la grille', 'N/A')}'")

                        # Récupération du pourcentage et du label pour l'année en cours
                        remise_pct, libelle_remise = self.get_discount_info(mois_factures + 1, grille)
                        montant_remise = round(prix_ht * (remise_pct / 100), 2)
                    except Exception as e:
                        logger.warning(f"    ⚠️  Impossible de récupérer la grille de remise: {str(e)}")

                prix_final = round(prix_ht - montant_remise, 2)

                if remise_pct > 0 and libelle_remise:
                    logger.info(f"    💰 Prix HT: {prix_ht}€ | Remise: {remise_pct}% ({libelle_remise}) | Final: {prix_final}€")
                else:
                    logger.info(f"    💰 Prix HT: {prix_ht}€ | Pas de remise")

                # Ajouter la ligne à la facture
                invoice_lines.append({
                    'product_id': int(product_id),
                    'service_name': service_name,
                    'prix_ht': prix_ht,
                    'remise_pct': remise_pct,
                    'libelle_remise': libelle_remise
                })

                # Mémoriser les mises à jour à faire
                services_to_update.append({
                    'record_id': record_id,
                    'mois_factures': mois_factures + 1,
                    'occurrences_restantes': max(0, occurrences_restantes - 1)
                })

            # Si aucune ligne valide, on arrête
            if not invoice_lines:
                logger.info(f"  ⏭️  Aucune ligne de facture valide pour ce groupe")
                return False

            # Mode dry-run : simulation uniquement
            if self.dry_run:
                logger.info(f"  🧪 MODE DRY-RUN: Facture non créée (test uniquement)")
                logger.info(f"     - Client ID: {client_id}")
                logger.info(f"     - Nombre de lignes: {len(invoice_lines)}")
                return True

            # Création de la facture groupée dans Sellsy
            logger.info(f"  📤 Envoi de la facture groupée à Sellsy v2...")
            result = self.sellsy.create_grouped_invoice(
                client_id=int(client_id),
                invoice_lines=invoice_lines
            )

            invoice_id = result.get('invoice_id')
            logger.info(f"  ✅ Facture groupée créée dans Sellsy ! (ID: {invoice_id})")
            logger.info(f"     Nombre de lignes: {len(invoice_lines)}")
            logger.info(f"  ⏸️  Facture en attente de validation (draft)")

            # Mise à jour des compteurs dans Airtable pour tous les services
            for update_info in services_to_update:
                self.airtable.update_service_counters(
                    record_id=update_info['record_id'],
                    mois_factures=update_info['mois_factures'],
                    occurrences_restantes=update_info['occurrences_restantes']
                )

            logger.info(f"  ✅ Compteurs mis à jour dans Airtable ({len(services_to_update)} services)")

            # Retourner l'ID de la facture créée
            return invoice_id

        except Exception as e:
            logger.error(f"  ❌ Échec de la création de la facture groupée")
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

            # Groupement des services par client et date
            grouped_services = self.group_services_by_client_and_date(services)
            logger.info(f"📦 {len(grouped_services)} facture(s) groupée(s) à créer")
            logger.info("")

            # Traitement de chaque groupe
            created_invoice_ids = []
            error_count = 0

            for (client_id, date_key), service_group in grouped_services.items():
                try:
                    invoice_id = self.process_grouped_subscription(client_id, date_key, service_group)
                    if invoice_id:
                        created_invoice_ids.append(invoice_id)
                    logger.info("")  # Ligne vide entre les groupes

                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Erreur: {str(e)}")
                    logger.info("")

            # Validation de toutes les factures créées
            if created_invoice_ids and not self.dry_run:
                logger.info("=" * 70)
                logger.info(f"🔄 VALIDATION DES FACTURES CRÉÉES ({len(created_invoice_ids)} facture(s))")
                logger.info("=" * 70)

                validated_count = 0
                validation_errors = 0

                for invoice_id in created_invoice_ids:
                    try:
                        logger.info(f"  🔄 Validation de la facture {invoice_id}...")
                        self.sellsy.validate_invoice(invoice_id)
                        logger.info(f"  ✅ Facture {invoice_id} validée (draft → due)")
                        validated_count += 1
                    except Exception as e:
                        logger.error(f"  ❌ Échec validation facture {invoice_id}: {str(e)}")
                        validation_errors += 1

                logger.info("")
                logger.info(f"✅ Factures validées: {validated_count}/{len(created_invoice_ids)}")
                if validation_errors > 0:
                    logger.warning(f"⚠️  Échecs de validation: {validation_errors}")
                logger.info("")

            # Résumé
            logger.info("=" * 70)
            logger.info("RÉSUMÉ DE LA SYNCHRONISATION")
            logger.info("=" * 70)
            logger.info(f"✅ Factures créées: {len(created_invoice_ids)}")
            if not self.dry_run and created_invoice_ids:
                logger.info(f"✅ Factures validées: {validated_count}/{len(created_invoice_ids)}")
            logger.info(f"❌ Échecs: {error_count}")
            logger.info(f"📊 Total services traités: {len(services)}")

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
