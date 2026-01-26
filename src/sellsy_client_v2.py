"""
Client Sellsy API v2 pour la création automatique de factures d'abonnement
OAuth2 moderne et REST standard (CONFORME DOC SELLSY V2)
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import requests


class SellsyClientV2:
    """Client pour interagir avec l'API Sellsy v2"""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

        self.token_url = "https://login.sellsy.com/oauth2/access-tokens"
        self.api_url = "https://api.sellsy.com/v2"

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        self._tva_cache: Optional[int] = None
        self._gocardless_cache: Optional[int] = None

    # ---------------------------------------------------------------------
    # AUTH
    # ---------------------------------------------------------------------

    def _get_access_token(self) -> str:
        """Récupère un token OAuth2 valide (avec cache)"""

        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token

        response = requests.post(
            self.token_url,
            json={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/json"},
            timeout=20,
        )

        if response.status_code != 200:
            raise Exception(
                f"Erreur OAuth Sellsy ({response.status_code}) - {response.text}"
            )

        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = datetime.now() + timedelta(
            seconds=data.get("expires_in", 3600)
        )

        return self._access_token

    # ---------------------------------------------------------------------
    # API CORE
    # ---------------------------------------------------------------------

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:

        token = self._get_access_token()

        response = requests.request(
            method=method,
            url=f"{self.api_url}{endpoint}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=data,
            params=params,
            timeout=30,
        )

        if response.status_code >= 400:
            raise Exception(
                f"Erreur API Sellsy v2: {response.status_code} - {response.text}"
            )

        return response.json()

    # ---------------------------------------------------------------------
    # METADATA
    # ---------------------------------------------------------------------

    def get_tva_20_id(self) -> int:
        """Retourne l'ID de la TVA à 20%"""

        if self._tva_cache:
            return self._tva_cache

        result = self._make_request("GET", "/taxes")

        for tax in result.get("data", []):
            if tax.get("is_active") and float(tax.get("rate", 0)) == 20:
                self._tva_cache = int(tax["id"])
                return self._tva_cache

        raise Exception("TVA 20% non trouvée dans Sellsy")

    def get_gocardless_payment_id(self) -> int:
        """Retourne l'ID GoCardless (env obligatoire)"""

        if self._gocardless_cache:
            return self._gocardless_cache

        payment_id = os.getenv("SELLSY_GOCARDLESS_PAYMENT_ID")
        if not payment_id:
            raise Exception(
                "Variable SELLSY_GOCARDLESS_PAYMENT_ID manquante"
            )

        self._gocardless_cache = int(payment_id)
        return self._gocardless_cache

    # ---------------------------------------------------------------------
    # FACTURATION
    # ---------------------------------------------------------------------

    def create_invoice(
        self,
        client_id: int,
        product_id: int,
        prix_ht: float,
        remise_pct: float,
        libelle_remise: str,
        service_name: str,
    ) -> Dict[str, Any]:
        """
        Crée une facture Sellsy v2

        Args:
            client_id: ID du client (company_id dans Sellsy)
            product_id: ID du produit dans le catalogue Sellsy
            prix_ht: Prix HT avant remise
            remise_pct: Pourcentage de remise
            libelle_remise: Libellé de la remise
            service_name: Nom du service

        Returns:
            Réponse avec invoice_id
        """

        tva_id = self.get_tva_20_id()

        montant_remise = round(prix_ht * (remise_pct / 100), 2)
        prix_final = round(prix_ht - montant_remise, 2)

        # ✅ LIGNE ARTICLE CATALOGUE (sans discount sur la ligne)
        rows = [
            {
                "type": "catalog",
                "related": {
                    "type": "product",
                    "id": int(product_id),
                },
                "quantity": "1",
                "unit_amount": str(prix_ht),
                "tax_id": tva_id,
            }
        ]

        # ✅ LIGNE REMISE SÉPARÉE (si remise > 0)
        if montant_remise > 0:
            rows.append(
                {
                    "type": "single",
                    "description": libelle_remise,
                    "unit_amount": str(-montant_remise),
                    "quantity": "1",
                    "tax_id": tva_id,
                }
            )

        # Détecter le type de client (company ou individual)
        client_info = self.get_client_info(int(client_id))
        client_type = client_info.get("_entity_type", "individual")

        invoice_data = {
            "status": "draft",
            "currency": "EUR",
            "subject": f"Abonnement mensuel - {service_name}",
            "note": "Retrouvez l'intégralité de vos factures dans votre espace abonné",
            "related": [
                {
                    "type": client_type,
                    "id": int(client_id),
                }
            ],
            "rows": rows,
            "use_lines_discount_conditions": False,
            "use_entity_discount_conditions": False,
            "discount_conditions": [],
            "settings": {
                "payments": {
                    "payment_modules": [],
                    "direct_debit_module": "gocardless"
                },
                "bank_account_visible": False
            }
        }

        # Debug
        import json
        print("📤 ENVOI SELLSY:")
        print(json.dumps(invoice_data, indent=2, ensure_ascii=False))

        result = self._make_request("POST", "/invoices", data=invoice_data)

        invoice_id = result.get("data", {}).get("id")

        # Finaliser et envoyer la facture
        try:
            # Marquer la facture comme envoyée (finaliser)
            self._make_request("PUT", f"/invoices/{invoice_id}", data={"status": "sent"})
            # Envoyer par email
            self.send_invoice_by_email(invoice_id)
            print(f"✅ Facture {invoice_id} finalisée et envoyée par email")
        except Exception as e:
            print(f"⚠️ Erreur lors de la finalisation/envoi de la facture {invoice_id}: {e}")

        return {
            "success": True,
            "invoice_id": invoice_id,
            "montant_ht": prix_final,
            "montant_remise": montant_remise,
        }

    def create_grouped_invoice(
        self,
        client_id: int,
        invoice_lines: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Crée une facture groupée Sellsy v2 avec plusieurs lignes de produits

        Args:
            client_id: ID du client (company_id dans Sellsy)
            invoice_lines: Liste de dictionnaires contenant:
                - product_id: ID du produit
                - service_name: Nom du service
                - prix_ht: Prix HT avant remise
                - remise_pct: Pourcentage de remise
                - libelle_remise: Libellé de la remise

        Returns:
            Réponse avec invoice_id
        """

        tva_id = self.get_tva_20_id()

        # Construction des lignes de facture
        rows = []
        montant_total_ht = 0
        montant_total_remise = 0

        for line in invoice_lines:
            product_id = line['product_id']
            prix_ht = line['prix_ht']
            remise_pct = line['remise_pct']
            libelle_remise = line.get('libelle_remise', '')

            montant_remise = round(prix_ht * (remise_pct / 100), 2)
            prix_final = round(prix_ht - montant_remise, 2)

            montant_total_ht += prix_final
            montant_total_remise += montant_remise

            # Ligne produit (sans discount sur la ligne)
            rows.append({
                "type": "catalog",
                "related": {
                    "type": "product",
                    "id": int(product_id),
                },
                "quantity": "1",
                "unit_amount": str(prix_ht),
                "tax_id": tva_id,
            })

            # Ligne remise séparée (si remise > 0)
            if montant_remise > 0:
                rows.append({
                    "type": "single",
                    "description": libelle_remise,
                    "unit_amount": str(-montant_remise),
                    "quantity": "1",
                    "tax_id": tva_id,
                })

        # Détecter le type de client
        client_info = self.get_client_info(int(client_id))
        client_type = client_info.get("_entity_type", "individual")

        # Créer un sujet descriptif
        if len(invoice_lines) == 1:
            subject = f"Abonnement mensuel - {invoice_lines[0]['service_name']}"
        else:
            subject = f"Abonnements mensuels ({len(invoice_lines)} services)"

        invoice_data = {
            "status": "draft",
            "currency": "EUR",
            "subject": subject,
            "note": "Retrouvez l'intégralité de vos factures dans votre espace abonné",
            "related": [
                {
                    "type": client_type,
                    "id": int(client_id),
                }
            ],
            "rows": rows,
            "use_lines_discount_conditions": False,
            "use_entity_discount_conditions": False,
            "discount_conditions": [],
            "settings": {
                "payments": {
                    "payment_modules": [],
                    "direct_debit_module": "gocardless"
                },
                "bank_account_visible": False
            }
        }

        # Debug
        import json
        print("📤 ENVOI SELLSY (FACTURE GROUPÉE):")
        print(json.dumps(invoice_data, indent=2, ensure_ascii=False))

        result = self._make_request("POST", "/invoices", data=invoice_data)

        invoice_id = result.get("data", {}).get("id")

        # Finaliser et envoyer la facture
        try:
            # Marquer la facture comme envoyée (finaliser)
            self._make_request("PUT", f"/invoices/{invoice_id}", data={"status": "sent"})
            # Envoyer par email
            self.send_invoice_by_email(invoice_id)
            print(f"✅ Facture groupée {invoice_id} finalisée et envoyée par email")
        except Exception as e:
            print(f"⚠️ Erreur lors de la finalisation/envoi de la facture groupée {invoice_id}: {e}")

        return {
            "success": True,
            "invoice_id": invoice_id,
            "montant_ht": montant_total_ht,
            "montant_remise": montant_total_remise,
            "nombre_lignes": len(invoice_lines),
        }

    def send_invoice_by_email(self, invoice_id: int) -> Dict[str, Any]:
        """
        Envoie une facture par email au client

        Args:
            invoice_id: ID de la facture dans Sellsy

        Returns:
            Réponse de l'API
        """
        result = self._make_request("POST", f"/invoices/{invoice_id}/send-by-email")
        return result

    # ---------------------------------------------------------------------
    # CLIENT
    # ---------------------------------------------------------------------

    def get_client_info(self, client_id: int) -> Dict[str, Any]:
        """Récupère les informations d'un client et son type (company ou individual)"""
        # Essayer d'abord en tant que company
        try:
            result = self._make_request("GET", f"/companies/{client_id}")
            data = result.get("data", {})
            data["_entity_type"] = "company"
            return data
        except Exception as e:
            # Si erreur, essayer en tant que individual (particulier)
            try:
                result = self._make_request("GET", f"/individuals/{client_id}")
                data = result.get("data", {})
                data["_entity_type"] = "individual"
                return data
            except Exception as e2:
                raise Exception(f"Client {client_id} introuvable (ni company ni individual): {e2}")


# -------------------------------------------------------------------------
# TEST
# -------------------------------------------------------------------------

def test_connection_v2():
    from dotenv import load_dotenv

    load_dotenv()

    client = SellsyClientV2(
        client_id=os.getenv("SELLSY_V2_CLIENT_ID"),
        client_secret=os.getenv("SELLSY_V2_CLIENT_SECRET"),
    )

    print("🧪 Test Sellsy API v2...")

    token = client._get_access_token()
    print(f"✅ Token OK: {token[:20]}...")

    tva = client.get_tva_20_id()
    print(f"✅ TVA 20% ID: {tva}")

    print("🎉 Sellsy API v2 prête à l'emploi")


if __name__ == "__main__":
    test_connection_v2()
