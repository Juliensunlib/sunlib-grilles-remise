import os
from src.sellsy_client_v2 import SellsyClientV2

client = SellsyClientV2(
    client_id=os.getenv('SELLSY_V2_CLIENT_ID'),
    client_secret=os.getenv('SELLSY_V2_CLIENT_SECRET')
)

# Cherche dans les moyens de paiement (à adapter selon l'API v2)
# Pour l'instant, récupère-le manuellement dans Sellsy :
# Menu > Réglages > Comptabilité > Journaux > Note l'ID du journal GoCardless
print("⚠️ Récupère l'ID GoCardless manuellement dans Sellsy pour l'instant")
