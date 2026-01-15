#!/usr/bin/env python3
"""
Client Sellsy pour la création de factures via l'API OAuth 1.0
"""

import json
import requests
from requests_oauthlib import OAuth1
from config import (
    SELLSY_CONSUMER_TOKEN,
    SELLSY_CONSUMER_SECRET,
    SELLSY_USER_TOKEN,
    SELLSY_USER_SECRET
)


class SellsyClient:
    """Client pour interagir avec l'API Sellsy"""
    
    API_URL = "https://apifeed.sellsy.com/0/"
    
    def __init__(self):
        """Initialise le client OAuth1 Sellsy"""
        if not all([
            SELLSY_CONSUMER_TOKEN,
            SELLSY_CONSUMER_SECRET,
            SELLSY_USER_TOKEN,
            SELLSY_USER_SECRET
        ]):
            raise ValueError("Toutes les variables Sellsy OAuth doivent être configurées")
        
        self.auth = OAuth1(
            SELLSY_CONSUMER_TOKEN,
            client_secret=SELLSY_CONSUMER_SECRET,
            resource_owner_key=SELLSY_USER_TOKEN,
            resource_owner_secret=SELLSY_USER_SECRET,
            signature_type='query'
        )
    
    def call_api(self, method, params):
        """
        Appelle l'API Sellsy
        
        Args:
            method: Méthode de l'API (ex: "Document.create")
            params: Paramètres de la requête
        
        Returns:
            dict: Réponse de l'API ou None en cas d'erreur
        """
        payload = {
            'request': 1,
            'io_mode': 'json',
            'do_in': json.dumps({
                'method': method,
                'params': params
            })
        }
        
        try:
            response = requests.post(
                self.API_URL,
                data=payload,
                auth=self.auth,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('status') == 'error':
                error_msg = result.get('error', 'Erreur inconnue')
                print(f"❌ Erreur API Sellsy: {error_msg}")
                return None
            
            return result.get('response', result)
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion à Sellsy: {e}")
            return None
        
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de parsing JSON: {e}")
            return None
    
    def create_invoice(self, client_id, item_id, rows, subject, displayed_date):
        """
        Crée une facture dans Sellsy
        
        Args:
            client_id: ID du client Sellsy
            item_id: ID du produit catalogue
            rows: Liste des lignes de la facture
            subject: Objet de la facture
            displayed_date: Date d'affichage de la facture (YYYY-MM-DD)
        
        Returns:
            dict: Réponse de l'API avec l'ID de la facture créée
        """
        params = {
            'document': {
                'doctype': 'invoice',
                'thirdid': client_id,
                'subject': subject,
                'displayedDate': displayed_date,
                'step': 'sent',
                'rows': rows
            }
        }
        
        return self.call_api('Document.create', params)
