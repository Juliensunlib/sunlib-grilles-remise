#!/usr/bin/env python3
"""
Script pour chercher des factures Sellsy avec différents critères
"""

import sys
import os
from dotenv import load_dotenv
from src.sellsy_client_v2 import SellsyClientV2

# Charger les variables d'environnement
load_dotenv()

def search_invoices(client, search_term=None, limit=50):
    """Cherche des factures selon un terme de recherche"""

    print(f"🔍 Recherche de factures (limite: {limit})...\n")

    try:
        # Récupérer les factures
        response = client._make_request("GET", "/invoices", params={
            "limit": limit,
            "offset": 0,
            "order": "desc",
            "direction": "created"
        })

        invoices = response.get('data', [])

        if not invoices:
            print("❌ Aucune facture trouvée")
            return []

        # Filtrer si un terme de recherche est fourni
        if search_term:
            search_term = search_term.lower()
            filtered = []
            for inv in invoices:
                # Chercher dans numéro, sujet, ID
                if (search_term in str(inv.get('id', '')).lower() or
                    search_term in str(inv.get('number', '')).lower() or
                    search_term in str(inv.get('subject', '')).lower()):
                    filtered.append(inv)
            invoices = filtered
            print(f"📌 Filtré sur '{search_term}': {len(invoices)} résultat(s)\n")

        if not invoices:
            print(f"❌ Aucune facture ne correspond à '{search_term}'")
            return []

        # Afficher les résultats
        print(f"{'ID':<10} {'Numéro':<20} {'Date':<12} {'Statut':<15} {'Montant TTC':<15} {'Sujet'}")
        print("=" * 120)

        for inv in invoices:
            inv_id = inv.get('id', '')
            number = inv.get('number', 'N/A')
            date = inv.get('date', 'N/A')
            status = inv.get('status', 'N/A')
            amount = inv.get('amounts', {}).get('total_incl_tax', '0')
            currency = inv.get('currency', 'EUR')
            subject = inv.get('subject', '')[:60]

            print(f"{inv_id:<10} {number:<20} {date:<12} {status:<15} {amount:>10} {currency:<3} {subject}")

        print(f"\n✅ {len(invoices)} facture(s) trouvée(s)")
        print("\n💡 Pour inspecter une facture en détail:")
        print("   python3 inspect_invoice.py <ID>")

        return invoices

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    # Récupérer les credentials
    client_id = os.getenv('SELLSY_V2_CLIENT_ID')
    client_secret = os.getenv('SELLSY_V2_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("❌ Variables SELLSY_V2_CLIENT_ID et SELLSY_V2_CLIENT_SECRET manquantes")
        print("\nAjoutez-les dans votre fichier .env:")
        print("SELLSY_V2_CLIENT_ID=votre_client_id")
        print("SELLSY_V2_CLIENT_SECRET=votre_client_secret")
        sys.exit(1)

    client = SellsyClientV2(client_id, client_secret)

    # Récupérer le terme de recherche depuis les arguments
    search_term = sys.argv[1] if len(sys.argv) > 1 else None
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    if search_term:
        print(f"🔎 Recherche: {search_term}\n")

    search_invoices(client, search_term, limit)

if __name__ == "__main__":
    main()
