#!/usr/bin/env python3
"""
Synchronisation automatique des factures d'abonnement mensuelles - V2.0
Crée les factures dans Sellsy avec remise progressive selon les grilles dynamiques

VERSION 2.0 - GRILLES DYNAMIQUES
- Les remises sont configurables dans Airtable (table grilles_remise)
- Possibilité de créer plusieurs grilles (VIP, régionales, promotions, etc.)
- Changement de stratégie sans modification de code

Usage:
    python sync_subscription_invoices.py
"""

import sys
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from pyairtable import Table
from airtable_client import AirtableClient
from sellsy_client import SellsyClient
from config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_ID,
    AIRTABLE_GRILLES_TABLE_NAME,
    DRY_RUN,
    validate_config
)

def log_message(message):
    """Affiche un message horodaté"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_grilles_table():
    """Initialise la connexion à la table grilles_remise"""
    return Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_GRILLES_TABLE_NAME)

def parse_grille(grille_record):
    """
    Parse un enregistrement de grille de remise
    
    Args:
        grille_record: Enregistrement Airtable de la grille
        
    Returns:
        dict: Données de la grille structurées
    """
    fields = grille_record['fields']
    
    return {
        'id': grille_record['id'],
        'name': fields.get('Nom de la grille', 'Grille sans nom'),
        'annee_1_pct': fields.get('Année 1 (%)', 0),
        'annee_2_pct': fields.get('Année 2 (%)', 0),
        'annee_3_pct': fields.get('Année 3+ (%)', 0),
        'label_annee_1': fields.get('Label Année 1', 'Remise Année 1'),
        'label_annee_2': fields.get('Label Année 2', 'Remise Année 2'),
        'label_annee_3': fields.get('Label Année 3+', 'Remise Année 3+'),
        'actif': fields.get('Actif', False)
    }

def get_discount_grid(grilles_table, service_record):
    """
    Récupère la grille de remise applicable pour un abonnement
    
    Ordre de priorité :
    1. Grille spécifique liée à l'abonnement
    2. Grille par défaut active
    3. Aucune remise si aucune grille trouvée
    
    Args:
        grilles_table: Instance de la table grilles_remise
        service_record: Enregistrement Airtable de l'abonnement
        
    Returns:
        dict: Données de la grille ou None
    """
    fields = service_record['fields']
    
    # Cas 1 : Grille spécifique liée à l'abonnement
    if 'Grille de remise' in fields and fields['Grille de remise']:
        grille_id = fields['Grille de remise'][0]
        try:
            grille_record = grilles_table.get(grille_id)
            grille = parse_grille(grille_record)
            
            # Vérifier que la grille est active
            if grille['actif']:
                log_message(f"  📊 Grille spécifique: '{grille['name']}'")
                return grille
            else:
                log_message(f"  ⚠️  Grille '{grille['name']}' inactive, utilisation de la grille par défaut")
        except Exception as e:
            log_message(f"  ⚠️  Erreur lors de la récupération de la grille spécifique: {e}")
    
    # Cas 2 : Grille par défaut
    try:
        formula = "AND({Grille par défaut} = TRUE(), {Actif} = TRUE())"
        grilles = grilles_table.all(formula=formula)
        
        if grilles:
            grille = parse_grille(grilles[0])
            log_message(f"  📊 Grille par défaut: '{grille['name']}'")
            return grille
    except Exception as e:
        log_message(f"  ⚠️  Erreur lors de la récupération de la grille par défaut: {e}")
    
    # Cas 3 : Aucune grille trouvée
    log_message(f"  ⚠️  Aucune grille de remise trouvée")
    return None

def calculate_discount_from_grid(prix_ht, mois_factures, grille):
    """
    Calcule la remise selon la grille dynamique
    
    Args:
        prix_ht: Prix mensuel HT (prix plein avant remise)
        mois_factures: Nombre de mois déjà facturés
        grille: Dictionnaire de la grille de remise ou None
        
    Returns:
        dict: {
            'discount_pct': % de remise,
            'discount_amount_ht': Montant de la remise en €,
            'discount_label': Label pour la ligne de remise,
            'final_amount_ht': Montant final après remise
        }
    """
    if not grille:
        return {
            'discount_pct': 0,
            'discount_amount_ht': 0,
            'discount_label': None,
            'final_amount_ht': prix_ht
        }
    
    # Déterminer l'année et récupérer la remise correspondante
    if mois_factures < 12:  # Année 1
        discount_pct = grille['annee_1_pct']
        discount_label = f"{grille['label_annee_1']} (-{discount_pct}%)" if discount_pct > 0 else None
    elif mois_factures < 24:  # Année 2
        discount_pct = grille['annee_2_pct']
        discount_label = f"{grille['label_annee_2']} (-{discount_pct}%)" if discount_pct > 0 else None
    else:  # Année 3+
        discount_pct = grille['annee_3_pct']
        discount_label = f"{grille['label_annee_3']} (-{discount_pct}%)" if discount_pct > 0 else None
    
    discount_amount_ht = prix_ht * (discount_pct / 100)
    final_amount_ht = prix_ht - discount_amount_ht
    
    return {
        'discount_pct': discount_pct,
        'discount_amount_ht': round(discount_amount_ht, 2),
        'discount_label': discount_label,
        'final_amount_ht': round(final_amount_ht, 2)
    }

def is_billing_due(date_debut, mois_factures):
    """
    Vérifie si une facture doit être créée aujourd'hui (date anniversaire)
    
    Args:
        date_debut: Date de début de l'abonnement (string ISO ou datetime)
        mois_factures: Nombre de mois déjà facturés
        
    Returns:
        bool: True si la facturation est due aujourd'hui
    """
    if not date_debut:
        return False
    
    # Convertir la date de début en datetime si c'est une string
    if isinstance(date_debut, str):
        date_debut = datetime.fromisoformat(date_debut.replace('Z', '+00:00')).date()
    elif isinstance(date_debut, datetime):
        date_debut = date_debut.date()
    
    # Calculer la date anniversaire du prochain mois à facturer
    date_anniversaire = date_debut + relativedelta(months=mois_factures)
    
    # Vérifier si c'est aujourd'hui
    today = date.today()
    
    log_message(f"  📅 Date début: {date_debut}, Mois facturés: {mois_factures}, "
                f"Date anniversaire: {date_anniversaire}, Aujourd'hui: {today}")
    
    return date_anniversaire == today

def create_subscription_invoice(sellsy_client, grilles_table, airtable_record):
    """
    Crée une facture d'abonnement dans Sellsy avec remise selon grille
    
    Args:
        sellsy_client: Instance de SellsyClient
        grilles_table: Instance de la table grilles_remise
        airtable_record: Enregistrement Airtable de l'abonnement
        
    Returns:
        dict: Réponse de l'API Sellsy ou None si échec
    """
    fields = airtable_record['fields']
    record_id = airtable_record['id']
    
    # Récupération des données
    nom_service = fields.get('Nom du service', 'Service sans nom')
    client_id = fields.get('ID_Sellsy_abonné')
    item_id = fields.get('ID Sellsy')
    prix_ht = fields.get('Prix HT')
    taux_tva = fields.get('Taux TVA', 20)
    mois_factures = fields.get('Mois facturés', 0)
    appliquer_remise = fields.get('Appliquer remise dégressive', False)
    
    # Validation des données obligatoires
    if not all([client_id, item_id, prix_ht]):
        log_message(f"  ⚠️ Données manquantes pour {nom_service}")
        return None
    
    # Récupération de la grille de remise si activée
    grille = None
    if appliquer_remise:
        grille = get_discount_grid(grilles_table, airtable_record)
    else:
        log_message(f"  ℹ️  Remise désactivée pour cet abonnement")
    
    # Calcul de la remise selon la grille
    discount_data = calculate_discount_from_grid(prix_ht, mois_factures, grille)
    
    log_message(f"  💰 Prix HT: {prix_ht}€ | Remise: {discount_data['discount_pct']}% | "
                f"Final: {discount_data['final_amount_ht']}€")
    
    # Mode dry-run : afficher ce qui serait fait sans créer
    if DRY_RUN:
        log_message(f"  🧪 MODE DRY-RUN: Facture non créée (test uniquement)")
        log_message(f"     - Client ID: {client_id}")
        log_message(f"     - Produit ID: {item_id}")
        log_message(f"     - Montant final: {discount_data['final_amount_ht']}€ HT")
        if discount_data['discount_label']:
            log_message(f"     - Remise: {discount_data['discount_label']}")
        return {'success': True, 'invoice_id': 'DRY_RUN_TEST', 'dry_run': True}
    
    # Construction des lignes de la facture
    rows = [
        {
            'itemid': item_id,  # Produit catalogue (prix + TVA auto)
            'qt': 1
        }
    ]
    
    # Ajouter la ligne de remise si applicable
    if discount_data['discount_pct'] > 0 and discount_data['discount_label']:
        rows.append({
            'name': discount_data['discount_label'],
            'unitAmount': -discount_data['discount_amount_ht'],  # Montant négatif
            'qt': 1,
            'taxrate': taux_tva
        })
    
    # Construction du payload Sellsy
    today_str = datetime.now().strftime('%Y-%m-%d')
    subject = f"Abonnement SunLib - Mois {mois_factures + 1}"
    
    # Appel API Sellsy
    try:
        log_message(f"  📤 Envoi de la facture à Sellsy...")
        response = sellsy_client.create_invoice(
            client_id=client_id,
            item_id=item_id,
            rows=rows,
            subject=subject,
            displayed_date=today_str
        )
        
        if response:
            invoice_id = response.get('docid') or response.get('doc_id')
            log_message(f"  ✅ Facture créée avec succès - ID Sellsy: {invoice_id}")
            return {
                'success': True,
                'invoice_id': invoice_id,
                'response': response
            }
        else:
            log_message(f"  ❌ Échec de création de la facture")
            return None
    
    except Exception as e:
        log_message(f"  ❌ Erreur lors de la création de la facture: {e}")
        return None

def update_airtable_counters(airtable_client, record_id, invoice_id=None):
    """
    Met à jour les compteurs dans Airtable après création de facture
    
    Args:
        airtable_client: Instance d'AirtableClient
        record_id: ID de l'enregistrement Airtable
        invoice_id: ID de la facture créée dans Sellsy
    """
    try:
        result = airtable_client.update_counters(record_id, invoice_id)
        fields = result['fields']
        
        log_message(f"  ✅ Compteurs mis à jour: Mois facturés = {fields['Mois facturés']}, "
                   f"Occurrences restantes = {fields['Occurrences restantes']}")
    
    except Exception as e:
        log_message(f"  ⚠️ Erreur lors de la mise à jour des compteurs: {e}")

def process_subscription_invoices():
    """
    Traite tous les abonnements éligibles pour facturation
    
    Critères d'éligibilité :
    - Date de début remplie et dans le passé
    - Occurrences restantes > 0
    - Date anniversaire = aujourd'hui
    """
    log_message("="*70)
    log_message("DÉMARRAGE DE LA SYNCHRONISATION DES FACTURES D'ABONNEMENT V2.0")
    log_message("="*70)
    
    # Valider la configuration
    try:
        validate_config()
    except ValueError as e:
        log_message(f"❌ ERREUR DE CONFIGURATION: {e}")
        sys.exit(1)
    
    try:
        # Initialiser les clients
        airtable_client = AirtableClient()
        sellsy_client = SellsyClient()
        grilles_table = get_grilles_table()
        
        log_message("✅ Connexion aux services établie")
        
        # Récupérer tous les abonnements actifs
        log_message("📊 Récupération des abonnements actifs depuis Airtable...")
        records = airtable_client.get_active_subscriptions()
        
        log_message(f"📋 Nombre d'abonnements actifs trouvés: {len(records)}")
        
        if not records:
            log_message("✅ Aucun abonnement à facturer aujourd'hui")
            return
        
        # Traiter chaque abonnement
        success_count = 0
        skipped_count = 0
        error_count = 0
        
        for record in records:
            fields = record['fields']
            nom_service = fields.get('Nom du service', 'Service sans nom')
            date_debut = fields.get('Date de début')
            mois_factures = fields.get('Mois facturés', 0)
            
            log_message(f"\n{'='*70}")
            log_message(f"📋 Traitement: {nom_service}")
            log_message(f"{'='*70}")
            
            # Vérifier si la facturation est due aujourd'hui
            if not is_billing_due(date_debut, mois_factures):
                log_message(f"  ⏭️  Pas de facturation aujourd'hui (date anniversaire différente)")
                skipped_count += 1
                continue
            
            # Créer la facture
            log_message(f"  🚀 Création de la facture...")
            result = create_subscription_invoice(sellsy_client, grilles_table, record)
            
            if result and result.get('success'):
                # Mettre à jour les compteurs dans Airtable (sauf en dry-run)
                if not result.get('dry_run'):
                    update_airtable_counters(
                        airtable_client, 
                        record['id'], 
                        result.get('invoice_id')
                    )
                success_count += 1
            else:
                log_message(f"  ❌ Échec de la création de la facture")
                error_count += 1
            
            # Pause pour éviter de surcharger les APIs
            time.sleep(1)
        
        # Résumé final
        log_message(f"\n{'='*70}")
        log_message("RÉSUMÉ DE LA SYNCHRONISATION")
        log_message(f"{'='*70}")
        log_message(f"✅ Factures créées avec succès: {success_count}")
        log_message(f"⏭️  Abonnements ignorés (pas aujourd'hui): {skipped_count}")
        log_message(f"❌ Échecs: {error_count}")
        log_message(f"{'='*70}\n")
    
    except Exception as e:
        log_message(f"❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Fonction principale"""
    process_subscription_invoices()

if __name__ == "__main__":
    main()
