"""
Client Sellsy API v1 pour la création automatique de factures d'abonnement
Gère l'authentification OAuth 1.0 et la création de factures avec remises dynamiques
"""

import os
import hashlib
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from requests_oauthlib import OAuth1


class SellsyClient:
    """Client pour interagir avec l'API Sellsy v1"""
    
    def __init__(self, consumer_token: str, consumer_secret: str, 
                 user_token: str, user_secret: str):
        """
        Initialise le client Sellsy avec les credentials OAuth 1.0
        
        Args:
            consumer_token: Consumer token de l'API Sellsy
            consumer_secret: Consumer secret de l'API Sellsy
            user_token: User token de l'API Sellsy
            user_secret: User secret de l'API Sellsy
        """
        self.api_url = 'https://apifeed.sellsy.com/0/'
        self.auth = OAuth1(
            consumer_token,
            consumer_secret,
            user_token,
            user_secret,
            signature_type='query'
        )
        
        # Cache pour les IDs récurrents
        self._tva_cache: Optional[str] = None
        self._gocardless_cache: Optional[str] = None
    
    def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue une requête à l'API Sellsy
        
        Args:
            method: Méthode de l'API à appeler (ex: 'Invoices.create')
            params: Paramètres de la méthode
            
        Returns:
            Réponse de l'API en dictionnaire
            
        Raises:
            Exception: Si l'API retourne une erreur
        """
        # Construction du payload avec do_in encodé en JSON string
        payload = {
            'request': '1',
            'io_mode': 'json',
            'do_in': json.dumps({
                'method': method,
                'params': params
            })
        }
        
        # Envoi en form-data (pas en JSON)
        response = requests.post(
            self.api_url,
            auth=self.auth,
            data=payload,  # ← data au lieu de json
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        data = response.json()
        
        # Gestion des erreurs API
        if 'error' in data:
            raise Exception(f"Erreur API Sellsy: {data['error']}")
        
        if response.status_code != 200:
            raise Exception(f"Erreur HTTP {response.status_code}: {response.text}")
        
        return data.get('response', data)
    
    def get_tva_20_id(self) -> str:
        """
        Récupère l'ID de la TVA à 20%
        Utilise un cache pour éviter les appels répétés
        
        Returns:
            ID de la TVA à 20%
            
        Raises:
            Exception: Si la TVA 20% n'est pas trouvée
        """
        if self._tva_cache:
            return self._tva_cache
        
        result = self._make_request('Tax.getList', {})
        
        for tax_id, tax_data in result.get('result', {}).items():
            if float(tax_data.get('value', 0)) == 20.0:
                self._tva_cache = str(tax_id)
                return self._tva_cache
        
        raise Exception("TVA à 20% non trouvée dans Sellsy")
    
    def get_gocardless_payment_id(self) -> str:
        """
        Récupère l'ID du moyen de paiement GoCardless
        Utilise un cache pour éviter les appels répétés
        
        Returns:
            ID du moyen de paiement GoCardless
            
        Raises:
            Exception: Si GoCardless n'est pas trouvé
        """
        if self._gocardless_cache:
            return self._gocardless_cache
        
        result = self._make_request('Accountdatas.getList', {
            'search': {
                'contains': 'gocardless'
            }
        })
        
        for payment_id, payment_data in result.get('result', {}).items():
            label = payment_data.get('label', '').lower()
            if 'gocardless' in label or 'sepa' in label:
                self._gocardless_cache = str(payment_id)
                return self._gocardless_cache
        
        raise Exception("Moyen de paiement GoCardless non trouvé dans Sellsy")
    
    def create_invoice(self, 
                      client_id: str,
                      product_id: str,
                      prix_ht: float,
                      remise_pct: float,
                      libelle_remise: str,
                      service_name: str) -> Dict[str, Any]:
        """
        Crée une facture dans Sellsy avec remise dynamique
        
        Args:
            client_id: ID du client dans Sellsy
            product_id: ID du produit/service dans Sellsy
            prix_ht: Prix HT du service (avant remise)
            remise_pct: Pourcentage de remise (0-100)
            libelle_remise: Libellé de la ligne de remise (ex: "🎉 Offre de lancement (-20%)")
            service_name: Nom du service (pour le logging)
            
        Returns:
            Réponse de l'API contenant l'ID de la facture créée
            
        Raises:
            Exception: Si la création échoue
        """
        # Récupération des IDs nécessaires (avec cache)
        tva_id = self.get_tva_20_id()
        gocardless_id = self.get_gocardless_payment_id()
        
        # Calcul du montant de la remise
        montant_remise = round(prix_ht * (remise_pct / 100), 2)
        prix_final = round(prix_ht - montant_remise, 2)
        
        # Construction des lignes de facture
        rows = []
        
        # Ligne 1 : Produit au prix plein
        rows.append({
            'row_type': 'item',
            'row_linkedid': str(product_id),
            'row_name': service_name,
            'row_unit': 'mois',
            'row_qt': 1,
            'row_unitAmount': prix_ht,
            'row_tax': tva_id
        })
        
        # Ligne 2 : Remise (seulement si remise > 0)
        if remise_pct > 0 and montant_remise > 0:
            rows.append({
                'row_type': 'once',
                'row_name': libelle_remise,
                'row_unit': '',
                'row_qt': 1,
                'row_unitAmount': -montant_remise,  # Négatif pour la remise
                'row_tax': tva_id
            })
        
        # Construction de la facture
        invoice_data = {
            'document': {
                'doctype': 'invoice',
                'thirdid': str(client_id),
                'displayedDate': int(time.time()),  # ✅ CORRECTION: Timestamp Unix
                'payMediumId': gocardless_id,
                'currency': 'EUR',
                'subject': f'Abonnement mensuel - {service_name}',
                'notes': 'Facture générée automatiquement'
            },
            'rows': rows
        }
        
        # Appel API
        result = self._make_request('Document.create', invoice_data)
        
        return {
            'invoice_id': result.get('doc_id'),
            'montant_ht': prix_final,
            'montant_remise': montant_remise,
            'success': True
        }
    
    def get_client_info(self, client_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un client
        
        Args:
            client_id: ID du client dans Sellsy
            
        Returns:
            Informations du client
        """
        result = self._make_request('Client.getOne', {
            'id': str(client_id)
        })
        
        return result.get('client', {})


def test_connection():
    """Test rapide de connexion à l'API Sellsy"""
    from dotenv import load_dotenv
    load_dotenv()
    
    client = SellsyClient(
        consumer_token=os.getenv('SELLSY_CONSUMER_TOKEN'),
        consumer_secret=os.getenv('SELLSY_CONSUMER_SECRET'),
        user_token=os.getenv('SELLSY_USER_TOKEN'),
        user_secret=os.getenv('SELLSY_USER_SECRET')
    )
    
    try:
        print("🧪 Test de connexion Sellsy...")
        tva_id = client.get_tva_20_id()
        print(f"✅ TVA 20% ID: {tva_id}")
        
        gocardless_id = client.get_gocardless_payment_id()
        print(f"✅ GoCardless ID: {gocardless_id}")
        
        print("✅ Connexion Sellsy OK !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == '__main__':
    test_connection()
