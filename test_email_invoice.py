#!/usr/bin/env python3
"""
Script de test pour découvrir l'endpoint d'envoi d'email Sellsy v2
"""

import sys
import os
from dotenv import load_dotenv
from src.sellsy_client_v2 import SellsyClientV2
import json

# Charger les variables d'environnement
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_email_invoice.py <invoice_id>")
        print("\nExemple: python test_email_invoice.py 3105")
        sys.exit(1)

    invoice_id = sys.argv[1]
    client = SellsyClientV2(
        client_id=os.getenv('SELLSY_V2_CLIENT_ID'),
        client_secret=os.getenv('SELLSY_V2_CLIENT_SECRET')
    )

    print(f"🧪 Test d'envoi d'email pour la facture #{invoice_id}...\n")

    # D'abord, récupérer les infos de la facture
    print("📋 Récupération des informations de la facture...")
    try:
        invoice = client._make_request("GET", f"/invoices/{invoice_id}")
        related = invoice.get('related', [])
        contact_id = next((r['id'] for r in related if r.get('type') == 'contact'), None)
        print(f"✓ Contact ID trouvé: {contact_id}")
    except Exception as e:
        print(f"❌ Impossible de récupérer la facture: {e}")
        return

    # Liste des endpoints et payloads à tester
    tests = [
        (f"/invoices/{invoice_id}/send", {}),
        (f"/invoices/{invoice_id}/send", {"contact_id": contact_id}),
        (f"/invoices/{invoice_id}/send", {"contact_ids": [contact_id]}),
        (f"/invoices/{invoice_id}/send", {"to": contact_id}),
        (f"/invoices/{invoice_id}/send-email", {}),
        (f"/invoices/{invoice_id}/send-email", {"contact_id": contact_id}),
        (f"/invoices/{invoice_id}/email", {}),
        (f"/invoices/{invoice_id}/email", {"contact_id": contact_id}),
    ]

    for endpoint, payload in tests:
        print(f"\n{'='*80}")
        print(f"Test: POST {endpoint}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
        print('='*80)

        try:
            result = client._make_request("POST", endpoint, data=payload)
            print("✅ SUCCESS!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"\n🎉 Configuration qui fonctionne:")
            print(f"   Endpoint: POST {endpoint}")
            print(f"   Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            return

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erreur: {error_msg[:200]}...")

            if "404" in error_msg:
                print("→ Endpoint inexistant")
            elif "400" in error_msg or "invalid" in error_msg.lower():
                print("→ Endpoint existe mais paramètres invalides")

    print(f"\n{'='*80}")
    print("❌ Aucun endpoint d'envoi d'email trouvé")
    print("='*80")
    print("\nPossibilités:")
    print("1. L'API Sellsy v2 ne permet pas l'envoi automatique d'emails")
    print("2. L'endpoint utilise un autre pattern (vérifier la doc officielle)")
    print("3. L'envoi nécessite des permissions spécifiques")

if __name__ == "__main__":
    main()
