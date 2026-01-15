"""
Client Airtable pour la gestion des abonnements et grilles de remise
"""

import os
from typing import Dict, List, Optional
import requests
from datetime import datetime


class AirtableClient:
    """Client pour interagir avec l'API Airtable"""
    
    def __init__(self, api_key: str, base_id: str, 
                 table_services: str = 'service_sellsy',
                 table_grilles: str = 'grilles_remise'):
        """
        Initialise le client Airtable
        
        Args:
            api_key: Clé API Airtable (commence par pat...)
            base_id: ID de la base Airtable
            table_services: Nom de la table des services (défaut: service_sellsy)
            table_grilles: Nom de la table des grilles de remise (défaut: grilles_remise)
        """
        self.api_key = api_key
        self.base_id = base_id
        self.table_services = table_services
        self.table_grilles = table_grilles
        self.base_url = f'https://api.airtable.com/v0/{base_id}'
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_eligible_subscriptions(self) -> List[Dict]:
        """
        Récupère tous les abonnements éligibles à la facturation
        
        Critères d'éligibilité :
        - Catégorie = "Abonnement"
        - Occurrences restantes > 0
        - Date de début renseignée
        
        Returns:
            Liste des abonnements éligibles
        """
        # Construction de la formule Airtable
        formula = "AND({Catégorie} = 'Abonnement', {Occurrences restantes} > 0, {Date de début} != '')"
        
        params = {
            'filterByFormula': formula,
            'view': 'Grid view'  # Vue par défaut
        }
        
        response = requests.get(
            f'{self.base_url}/{self.table_services}',
            headers=self.headers,
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur Airtable: {response.status_code} - {response.text}")
        
        data = response.json()
        return data.get('records', [])
    
    def get_discount_grids(self) -> List[Dict]:
        """
        Récupère toutes les grilles de remise actives
        
        Returns:
            Liste des grilles de remise
        """
        response = requests.get(
            f'{self.base_url}/{self.table_grilles}',
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur Airtable: {response.status_code} - {response.text}")
        
        data = response.json()
        records = data.get('records', [])
        
        # Retourne uniquement les champs
        return [record['fields'] for record in records]
    
    def get_discount_grid(self, grid_id: str) -> Dict:
        """
        Récupère une grille de remise spécifique par son ID
        
        Args:
            grid_id: ID de la grille de remise dans Airtable
            
        Returns:
            Données de la grille de remise
        """
        response = requests.get(
            f'{self.base_url}/{self.table_grilles}/{grid_id}',
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur Airtable: {response.status_code} - {response.text}")
        
        data = response.json()
        return data.get('fields', {})
    
    def update_service_counters(self, record_id: str, 
                                mois_factures: int,
                                occurrences_restantes: int) -> bool:
        """
        Met à jour les compteurs d'un service après facturation
        
        Args:
            record_id: ID du record Airtable à mettre à jour
            mois_factures: Nouveau nombre de mois facturés
            occurrences_restantes: Nouveau nombre d'occurrences restantes
            
        Returns:
            True si la mise à jour a réussi
        """
        payload = {
            'fields': {
                'Mois facturés': mois_factures,
                'Occurrences restantes': occurrences_restantes
            }
        }
        
        response = requests.patch(
            f'{self.base_url}/{self.table_services}/{record_id}',
            headers=self.headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur Airtable: {response.status_code} - {response.text}")
        
        return True
    
    def get_service(self, record_id: str) -> Dict:
        """
        Récupère un service spécifique par son ID
        
        Args:
            record_id: ID du service dans Airtable
            
        Returns:
            Données du service
        """
        response = requests.get(
            f'{self.base_url}/{self.table_services}/{record_id}',
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur Airtable: {response.status_code} - {response.text}")
        
        return response.json()


def test_connection():
    """Test rapide de connexion à Airtable"""
    from dotenv import load_dotenv
    load_dotenv()
    
    client = AirtableClient(
        api_key=os.getenv('AIRTABLE_API_KEY'),
        base_id=os.getenv('AIRTABLE_BASE_ID'),
        table_services=os.getenv('AIRTABLE_TABLE_NAME', 'service_sellsy'),
        table_grilles=os.getenv('AIRTABLE_GRILLES_TABLE_NAME', 'grilles_remise')
    )
    
    try:
        print("🧪 Test de connexion Airtable...")
        
        services = client.get_eligible_subscriptions()
        print(f"✅ {len(services)} abonnement(s) éligible(s) trouvé(s)")
        
        grilles = client.get_discount_grids()
        print(f"✅ {len(grilles)} grille(s) de remise trouvée(s)")
        
        print("✅ Connexion Airtable OK !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == '__main__':
    test_connection()
