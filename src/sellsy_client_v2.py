"""
Client Sellsy API v2 pour la création automatique de factures d'abonnement
OAuth2 moderne et REST standard
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests


class SellsyClientV2:
    """Client pour interagir avec l'API Sellsy v2"""
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialise le client Sellsy avec OAuth2
        
        Args:
            client_id: Client ID de l'API Sellsy v2
            client_secret: Client Secret de l'API Sellsy v2
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = 'https://login.sellsy.com/oauth2/access-tokens'
        self.api_url = 'https://api.sellsy.com/v2'
        
        # Token management
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Cache
        self._tva_cache: Optional[str] = None
        self._gocardless_cache: Optional[str] = None
    
    def _get_access_token(self) -> str:
        """
        Récupère un access token valide (avec cache et refresh automatique)
        
        Returns:
            Access token Bearer
        """
        # Si token encore valide (marge de 5 min), on le réutilise
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token
        
        # Sinon, on demande un nouveau token
        response = requests.post(
            self.token_url,
            json={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur auth Sellsy: {response.status_code} - {response.text}")
        
        data = response.json()
        self._access_token = data['access_token']
        expires_in = data.get('expires_in', 3600)  # Défaut 1h
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        return self._access_token
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue une requête à l'API Sellsy v2
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Endpoint sans le /v2 (ex: '/taxes')
            data: Corps de la requête (JSON)
            params: Query parameters
            
        Returns:
            Réponse JSON
        """
        token = self._get_access_token()
        url = f"{self.api_url}{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        )
        
        if response.status_code >= 400:
            raise Exception(f"Erreur API Sellsy v2: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_tva_20_id(self) -> int:
        """
        Récupère l'ID de la TVA à 20% via l'API v2
        
        Returns:
            ID de la TVA à 20%
        """
        if self._tva_cache:
            return int(self._tva_cache)
        
        # GET /v2/taxes
        result = self._make_request('GET', '/taxes')
        
        for tax in result.get('data', []):
            if tax.get('is_active', False) and tax.get('rate', 0) == 20:
                self._tva_cache = str(tax['id'])
                return int(self._tva_cache)
        
        raise Exception("TVA à 20% non trouvée dans Sellsy")
    
    def get_gocardless_payment_id(self) -> int:
        """
        Récupère l'ID du moyen de paiement GoCardless
        Note: Peut nécessiter un endpoint spécifique v2 (à vérifier dans la doc)
        
        Returns:
            ID du moyen de paiement GoCardless
        """
        if self._gocardless_cache:
            return int(self._gocardless_cache)
        
        # TODO: Vérifier l'endpoint exact pour les moyens de paiement en v2
        # Potentiellement : GET /v2/payment-methods ou GET /v2/account-data
        
        # Pour l'instant, utilise un ID en dur (à récupérer manuellement)
        gocardless_id = os.getenv('SELLSY_GOCARDLESS_PAYMENT_ID')
        
        if not gocardless_id:
            raise Exception("Variable SELLSY_GOCARDLESS_PAYMENT_ID manquante")
        
        self._gocardless_cache = gocardless_id
        return int(gocardless_id)
    
    def create_invoice(self, 
                      company_id: int,
                      product_id: int,
                      prix_ht: float,
                      remise_pct: float,
                      libelle_remise: str,
                      service_name: str) -> Dict[str, Any]:
        """
        Crée une facture dans Sellsy via API v2
        
        Args:
            company_id: ID de l'entreprise/client dans Sellsy
            product_id: ID du produit (pour référence)
            prix_ht: Prix HT avant remise
            remise_pct: Pourcentage de remise
            libelle_remise: Libellé de la remise
            service_name: Nom du service
            
        Returns:
            Réponse avec invoice_id
        """
        tva_id = self.get_tva_20_id()
        
        # Calcul montants
        montant_remise = round(prix_ht * (remise_pct / 100), 2)
        prix_final = round(prix_ht - montant_remise, 2)
        
        # Construction des lignes de facture
        lines = [
            {
                "type": "standard",
                "label": service_name,
                "unit_amount": prix_ht,
                "quantity": 1,
                "tax_id": tva_id,
                "unit": "mois"
            }
        ]
        
        # Ligne de remise si applicable
        if remise_pct > 0:
            lines.append({
                "type": "standard",
                "label": libelle_remise,
                "unit_amount": -montant_remise,
                "quantity": 1,
                "tax_id": tva_id
            })
        
        # Construction de la facture
        invoice_data = {
            "company_id": company_id,
            "currency": "EUR",
            "subject": f"Abonnement mensuel - {service_name}",
            "notes": "Facture générée automatiquement",
            "lines": lines
        }
        
        # Appel API
        result = self._make_request('POST', '/invoices', data=invoice_data)
        
        return {
            'invoice_id': result.get('data', {}).get('id'),
            'montant_ht': prix_final,
            'montant_remise': montant_remise,
            'success': True
        }


def test_connection_v2():
    """Test de connexion à l'API Sellsy v2"""
    from dotenv import load_dotenv
    load_dotenv()
    
    client = SellsyClientV2(
        client_id=os.getenv('SELLSY_V2_CLIENT_ID'),
        client_secret=os.getenv('SELLSY_V2_CLIENT_SECRET')
    )
    
    try:
        print("🧪 Test de connexion Sellsy API v2...")
        
        # Test auth
        token = client._get_access_token()
        print(f"✅ Token obtenu: {token[:20]}...")
        
        # Test récupération TVA
        tva_id = client.get_tva_20_id()
        print(f"✅ TVA 20% ID: {tva_id}")
        
        print("✅ Connexion Sellsy v2 OK !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_connection_v2()
