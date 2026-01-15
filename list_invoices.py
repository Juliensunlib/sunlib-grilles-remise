#!/usr/bin/env python3
"""
Script pour lister les factures Sellsy existantes
"""

from src.sellsy_client_v2 import SellsyClientV2
from datetime import datetime, timedelta

def main():
    client = SellsyClientV2()

    print("🔍 Récupération des dernières factures...\n")

    try:
        # Récupérer les 20 dernières factures
        response = client.get("/invoices", params={
            "limit": 20,
            "offset": 0,
            "order": "desc",
            "direction": "created"
        })

        invoices = response.get('data', [])

        if not invoices:
            print("❌ Aucune facture trouvée")
            return

        print(f"{'ID':<10} {'Numéro':<20} {'Date':<12} {'Statut':<15} {'Montant TTC':<15} {'Sujet'}")
        print("=" * 110)

        for inv in invoices:
            inv_id = inv.get('id', '')
            number = inv.get('number', 'N/A')
            date = inv.get('date', 'N/A')
            status = inv.get('status', 'N/A')
            amount = inv.get('amounts', {}).get('total_incl_tax', '0')
            currency = inv.get('currency', 'EUR')
            subject = inv.get('subject', '')[:50]

            print(f"{inv_id:<10} {number:<20} {date:<12} {status:<15} {amount:>10} {currency:<3} {subject}")

        print(f"\n✅ {len(invoices)} factures récupérées")
        print("\n💡 Pour inspecter une facture en détail:")
        print("   python inspect_invoice.py <ID>")
        print(f"\n   Exemple: python inspect_invoice.py {invoices[0].get('id')}")

    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
