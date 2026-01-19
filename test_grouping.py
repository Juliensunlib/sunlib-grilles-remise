"""
Test de la fonctionnalité de groupement des factures
Affiche comment les services sont regroupés par client et date
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict

# Données de test simulant Airtable
test_services = [
    {
        'id': 'rec001',
        'fields': {
            'Nom du service': 'Hébergement Standard',
            'ID_Sellsy_abonné': '12345',
            'ID Sellsy': '100',
            'Prix HT': 50.0,
            'Date de début': '2025-01-01',
            'Mois facturés': 0,
            'Occurrences restantes': 12
        }
    },
    {
        'id': 'rec002',
        'fields': {
            'Nom du service': 'Maintenance Premium',
            'ID_Sellsy_abonné': '12345',  # Même client
            'ID Sellsy': '101',
            'Prix HT': 80.0,
            'Date de début': '2025-01-01',  # Même date
            'Mois facturés': 0,
            'Occurrences restantes': 12
        }
    },
    {
        'id': 'rec003',
        'fields': {
            'Nom du service': 'Support Pro',
            'ID_Sellsy_abonné': '67890',  # Client différent
            'ID Sellsy': '102',
            'Prix HT': 120.0,
            'Date de début': '2025-01-01',
            'Mois facturés': 0,
            'Occurrences restantes': 12
        }
    },
    {
        'id': 'rec004',
        'fields': {
            'Nom du service': 'Hébergement VPS',
            'ID_Sellsy_abonné': '12345',  # Même client que rec001 et rec002
            'ID Sellsy': '103',
            'Prix HT': 150.0,
            'Date de début': '2025-02-01',  # Date différente
            'Mois facturés': 0,
            'Occurrences restantes': 12
        }
    }
]


def group_services_by_client_and_date(services):
    """Groupe les services par (client_id, date_facturation)"""
    grouped = defaultdict(list)

    for service in services:
        fields = service['fields']
        client_id = fields.get('ID_Sellsy_abonné')
        date_debut = fields.get('Date de début')
        mois_factures = fields.get('Mois facturés', 0)

        if client_id and date_debut:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
            date_facturation = date_debut_obj + relativedelta(months=mois_factures + 1)
            date_key = date_facturation.strftime('%Y-%m')

            key = (str(client_id), date_key)
            grouped[key].append(service)

    return dict(grouped)


def main():
    print("=" * 70)
    print("🧪 TEST DE GROUPEMENT DES FACTURES")
    print("=" * 70)
    print()

    print(f"📊 Services à traiter : {len(test_services)}")
    print()

    for i, service in enumerate(test_services, 1):
        fields = service['fields']
        print(f"{i}. {fields['Nom du service']}")
        print(f"   Client: {fields['ID_Sellsy_abonné']}, Date: {fields['Date de début']}")

    print()
    print("=" * 70)
    print("📦 RÉSULTAT DU GROUPEMENT")
    print("=" * 70)
    print()

    grouped = group_services_by_client_and_date(test_services)

    print(f"✅ {len(grouped)} facture(s) groupée(s) à créer")
    print()

    for i, ((client_id, date_key), services) in enumerate(grouped.items(), 1):
        print(f"📄 Facture {i} - Client {client_id} - Date {date_key}")
        print(f"   Nombre de lignes: {len(services)}")

        total_ht = 0
        for service in services:
            fields = service['fields']
            print(f"   • {fields['Nom du service']} - {fields['Prix HT']}€ HT")
            total_ht += fields['Prix HT']

        print(f"   💰 Total HT: {total_ht}€")
        print()

    print("=" * 70)
    print("✅ Test terminé !")
    print("=" * 70)


if __name__ == '__main__':
    main()
