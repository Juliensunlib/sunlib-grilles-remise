#!/usr/bin/env python3
"""
Script pour inspecter la structure d'une facture Sellsy existante
et comprendre le format exact des lignes (rows)
"""

import sys
from src.sellsy_client_v2 import SellsyClientV2
import json

def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_invoice.py <invoice_id>")
        print("\nExemple: python inspect_invoice.py 12345")
        sys.exit(1)

    invoice_id = sys.argv[1]
    client = SellsyClientV2()

    print(f"🔍 Récupération de la facture #{invoice_id}...\n")

    try:
        # Récupérer la facture avec tous les détails
        invoice = client.get(f"/invoices/{invoice_id}")

        print("=" * 80)
        print("INFORMATIONS GÉNÉRALES")
        print("=" * 80)
        print(f"Numéro: {invoice.get('number')}")
        print(f"Date: {invoice.get('date')}")
        print(f"Sujet: {invoice.get('subject')}")
        print(f"Statut: {invoice.get('status')}")
        print(f"\nMontant total HT: {invoice.get('amounts', {}).get('total_excl_tax')} {invoice.get('currency')}")
        print(f"Montant total TTC: {invoice.get('amounts', {}).get('total_incl_tax')} {invoice.get('currency')}")

        # Afficher les lignes en détail
        rows = invoice.get('rows', [])
        print(f"\n{'=' * 80}")
        print(f"LIGNES DE FACTURE ({len(rows)} lignes)")
        print("=" * 80)

        for i, row in enumerate(rows, 1):
            print(f"\n--- Ligne {i} ---")
            print(json.dumps(row, indent=2, ensure_ascii=False))

        # Afficher les relations (related)
        related = invoice.get('related', [])
        if related:
            print(f"\n{'=' * 80}")
            print("RELATIONS")
            print("=" * 80)
            for rel in related:
                print(json.dumps(rel, indent=2, ensure_ascii=False))

        # Sauvegarder dans un fichier pour analyse détaillée
        output_file = f"invoice_{invoice_id}_dump.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(invoice, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Facture complète sauvegardée dans: {output_file}")

    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
