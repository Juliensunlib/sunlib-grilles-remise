#!/usr/bin/env python3
"""
Configuration centralisée pour la synchronisation des factures d'abonnement

Les variables sont lues depuis les variables d'environnement (GitHub Actions)
ou depuis un fichier .env pour les tests locaux.
"""

import os
from pathlib import Path

# Tentative de chargement du .env pour les tests locaux
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("📄 Fichier .env chargé pour test local")
except ImportError:
    # python-dotenv non installé (pas grave en production)
    pass

# =============================================================================
# CONFIGURATION AIRTABLE
# =============================================================================

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'service_sellsy')
AIRTABLE_GRILLES_TABLE_NAME = os.getenv('AIRTABLE_GRILLES_TABLE_NAME', 'grilles_remise')

# =============================================================================
# CONFIGURATION SELLSY (OAuth 1.0)
# =============================================================================

SELLSY_CONSUMER_TOKEN = os.getenv('SELLSY_CONSUMER_TOKEN')
SELLSY_CONSUMER_SECRET = os.getenv('SELLSY_CONSUMER_SECRET')
SELLSY_USER_TOKEN = os.getenv('SELLSY_USER_TOKEN')
SELLSY_USER_SECRET = os.getenv('SELLSY_USER_SECRET')

# =============================================================================
# OPTIONS
# =============================================================================

# Mode dry-run : affiche ce qui serait fait sans rien créer
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

# =============================================================================
# VALIDATION
# =============================================================================

def validate_config():
    """
    Valide que toutes les variables obligatoires sont configurées
    
    Raises:
        ValueError: Si une variable obligatoire est manquante
    """
    required_vars = {
        'AIRTABLE_API_KEY': AIRTABLE_API_KEY,
        'AIRTABLE_BASE_ID': AIRTABLE_BASE_ID,
        'SELLSY_CONSUMER_TOKEN': SELLSY_CONSUMER_TOKEN,
        'SELLSY_CONSUMER_SECRET': SELLSY_CONSUMER_SECRET,
        'SELLSY_USER_TOKEN': SELLSY_USER_TOKEN,
        'SELLSY_USER_SECRET': SELLSY_USER_SECRET,
    }
    
    missing_vars = [name for name, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}\n"
            f"Configurez ces variables dans GitHub Secrets ou dans un fichier .env local"
        )
    
    print("✅ Configuration validée avec succès")
    print(f"📊 Base Airtable: {AIRTABLE_BASE_ID}")
    print(f"📋 Table services: {AIRTABLE_TABLE_NAME}")
    print(f"📊 Table grilles: {AIRTABLE_GRILLES_TABLE_NAME}")
    
    if DRY_RUN:
        print("🧪 MODE DRY-RUN ACTIVÉ - Aucune facture ne sera créée")


if __name__ == '__main__':
    validate_config()
