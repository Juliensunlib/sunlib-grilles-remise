#!/usr/bin/env python3
"""
Script pour inspecter un client Sellsy et trouver où se trouve le mandate_id GoCardless
"""

import os
import json
from dotenv import load_dotenv
from src.sellsy_client_v2 import SellsyClientV2

load_dotenv()

def inspect_client(client_id: int):
    """Inspecte toutes les informations d'un client pour trouver le mandate_id"""

    client = SellsyClientV2(
        client_id=os.getenv('SELLSY_V2_CLIENT_ID'),
        client_secret=os.getenv('SELLSY_V2_CLIENT_SECRET')
    )

    print(f"\n{'='*80}")
    print(f"🔍 INSPECTION CLIENT SELLSY ID: {client_id}")
    print(f"{'='*80}\n")

    # 1. Informations client de base
    print("📋 1. INFORMATIONS CLIENT DE BASE")
    print("-" * 80)
    try:
        client_info = client.get_client_info(client_id)
        print(json.dumps(client_info, indent=2, ensure_ascii=False))

        # Recherche de champs liés à GoCardless
        print("\n🔎 Recherche de champs GoCardless dans client_info:")
        for key, value in client_info.items():
            if 'gocardless' in str(key).lower() or 'mandate' in str(key).lower():
                print(f"  ✓ Trouvé: {key} = {value}")

    except Exception as e:
        print(f"❌ Erreur: {e}")

    # 2. Tentative de récupérer les payment methods
    print(f"\n\n📋 2. PAYMENT METHODS (si disponible)")
    print("-" * 80)
    try:
        # Essayer différents endpoints possibles
        endpoints = [
            f"/companies/{client_id}/payment-methods",
            f"/individuals/{client_id}/payment-methods",
            f"/payment-methods?company_id={client_id}",
        ]

        for endpoint in endpoints:
            try:
                print(f"\n🔍 Test endpoint: {endpoint}")
                result = client._make_request("GET", endpoint)
                print(json.dumps(result, indent=2, ensure_ascii=False))

                # Recherche de champs GoCardless
                print("\n🔎 Recherche de champs GoCardless dans payment methods:")
                result_str = json.dumps(result, ensure_ascii=False).lower()
                if 'gocardless' in result_str or 'mandate' in result_str:
                    print("  ✓ Mention de GoCardless/mandate trouvée!")
                break

            except Exception as e:
                print(f"  ⚠️ Endpoint non disponible: {e}")
                continue

    except Exception as e:
        print(f"❌ Erreur générale: {e}")

    # 3. Recherche dans les custom fields
    print(f"\n\n📋 3. CUSTOM FIELDS")
    print("-" * 80)
    try:
        if 'custom_fields' in client_info:
            print("✓ Custom fields trouvés:")
            print(json.dumps(client_info['custom_fields'], indent=2, ensure_ascii=False))
        else:
            print("⚠️ Pas de custom_fields dans client_info")
    except Exception as e:
        print(f"❌ Erreur: {e}")

    # 4. Recherche dans les contacts/relations
    print(f"\n\n📋 4. RELATIONS/CONTACTS")
    print("-" * 80)
    try:
        if 'contacts' in client_info:
            print("✓ Contacts trouvés:")
            print(json.dumps(client_info['contacts'], indent=2, ensure_ascii=False))
        else:
            print("⚠️ Pas de contacts dans client_info")

        if 'related' in client_info:
            print("✓ Relations trouvées:")
            print(json.dumps(client_info['related'], indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erreur: {e}")

    # 5. Liste des factures du client pour voir si mandate_id apparaît
    print(f"\n\n📋 5. DERNIÈRES FACTURES DU CLIENT")
    print("-" * 80)
    try:
        # Récupérer les factures liées à ce client
        result = client._make_request(
            "GET",
            "/invoices",
            params={"related_id": client_id, "limit": 3}
        )

        invoices = result.get('data', [])
        print(f"✓ Nombre de factures trouvées: {len(invoices)}")

        if invoices:
            print("\n🔍 Inspection de la première facture:")
            print(json.dumps(invoices[0], indent=2, ensure_ascii=False))

            # Recherche de champs GoCardless dans les factures
            print("\n🔎 Recherche de champs GoCardless dans les factures:")
            invoice_str = json.dumps(invoices[0], ensure_ascii=False).lower()
            if 'gocardless' in invoice_str or 'mandate' in invoice_str:
                print("  ✓ Mention de GoCardless/mandate trouvée dans les factures!")
        else:
            print("⚠️ Aucune facture trouvée pour ce client")

    except Exception as e:
        print(f"❌ Erreur: {e}")

    print(f"\n{'='*80}")
    print("✅ INSPECTION TERMINÉE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # ID client à inspecter (fourni par l'utilisateur)
    CLIENT_ID = 722

    inspect_client(CLIENT_ID)
