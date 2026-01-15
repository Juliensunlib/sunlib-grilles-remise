#!/usr/bin/env python3
"""
Client Airtable pour la synchronisation des factures d'abonnement
"""

from pyairtable import Table
from config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_ID,
    AIRTABLE_TABLE_NAME
)


class AirtableClient:
    """Client pour interagir avec Airtable"""
    
    def __init__(self):
        """Initialise la connexion à Airtable"""
        if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
            raise ValueError("AIRTABLE_API_KEY et AIRTABLE_BASE_ID doivent être configurés")
        
        self.table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    
    def get_active_subscriptions(self):
        """
        Récupère tous les abonnements actifs
        
        Critères :
        - Catégorie = "Abonnement"
        - Occurrences restantes > 0
        - Date de début remplie
        
        Returns:
            list: Liste des enregistrements Airtable
        """
        formula = """
        AND(
            {Catégorie} = 'Abonnement',
            {Occurrences restantes} > 0,
            {Date de début} != BLANK()
        )
        """
        
        return self.table.all(formula=formula)
    
    def update_counters(self, record_id, invoice_id=None):
        """
        Met à jour les compteurs après création de facture
        
        Args:
            record_id: ID de l'enregistrement Airtable
            invoice_id: ID de la facture créée dans Sellsy (optionnel)
        
        Returns:
            dict: Enregistrement mis à jour
        """
        # Récupérer l'enregistrement actuel
        record = self.table.get(record_id)
        fields = record['fields']
        
        mois_factures = fields.get('Mois facturés', 0)
        occurrences_restantes = fields.get('Occurrences restantes', 0)
        
        # Préparer les mises à jour
        updates = {
            'Mois facturés': mois_factures + 1,
            'Occurrences restantes': max(0, occurrences_restantes - 1)
        }
        
        if invoice_id:
            from datetime import datetime
            updates['Dernière synchronisation'] = datetime.now().isoformat()
        
        # Appliquer les mises à jour
        return self.table.update(record_id, updates)


if __name__ == '__main__':
    # Test de connexion
    client = AirtableClient()
    print("✅ Connexion à Airtable réussie")
    
    subscriptions = client.get_active_subscriptions()
    print(f"📊 {len(subscriptions)} abonnements actifs trouvés")
