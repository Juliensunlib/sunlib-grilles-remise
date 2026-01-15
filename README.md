# 🚀 Système de Facturation Automatique V2.0 - Grilles Dynamiques

Système automatisé de création de factures d'abonnement mensuelles dans Sellsy avec remises progressives configurables dans Airtable.

## 🎯 Nouveautés V2.0

✅ **Grilles de remise configurables** - Plus besoin de modifier le code !  
✅ **Multi-grilles** - VIP, régionales, promotions, test A/B  
✅ **Historique** - Traçabilité complète dans Airtable  
✅ **Temps réel** - Changements instantanés, pas de redéploiement

---

## 📊 Architecture

### Flux complet

```
AIRTABLE (service_sellsy)
    ↓ Abonnements actifs (Occurrences restantes > 0)
    ↓ Date anniversaire = aujourd'hui
GITHUB ACTIONS (Workflow quotidien 9h UTC)
    ↓ Lecture table grilles_remise
    ↓ Calcul remises selon année d'abonnement
SELLSY API
    ↓ Création facture avec remise
    ↓ Statut = "Envoyé" → Prélèvement GoCardless auto
AIRTABLE
    ↓ Mise à jour compteurs (Mois facturés +1, Occurrences restantes -1)
```

---

## 🗂️ Structure du projet

```
.
├── .github/
│   └── workflows/
│       ├── sync_subscription_invoices_sandbox.yml  ← Workflow sandbox
│       └── sync_subscription_invoices_prod.yml     ← Workflow production
├── config.py                  ← Configuration centralisée
├── airtable_client.py         ← Client Airtable
├── sellsy_client.py           ← Client Sellsy OAuth 1.0
├── sync_subscription_invoices.py  ← Code principal V2.0
├── requirements.txt           ← Dépendances Python
└── README.md                  ← Ce fichier
```

---

## ⚙️ Configuration GitHub Secrets

### Secrets SANDBOX

```
AIRTABLE_API_KEY_SANDBOX          # Token API Airtable sandbox
AIRTABLE_BASE_ID_SANDBOX          # ID base Airtable sandbox (appU1s2od2kuHUpi2)
SELLSY_CONSUMER_TOKEN_SANDBOX     # Token OAuth Sellsy
SELLSY_CONSUMER_SECRET_SANDBOX    # Secret OAuth Sellsy
SELLSY_USER_TOKEN_SANDBOX         # User token Sellsy
SELLSY_USER_SECRET_SANDBOX        # User secret Sellsy
```

### Secrets PRODUCTION (à créer après validation sandbox)

```
AIRTABLE_API_KEY_PROD
AIRTABLE_BASE_ID_PROD
SELLSY_CONSUMER_TOKEN_PROD
SELLSY_CONSUMER_SECRET_PROD
SELLSY_USER_TOKEN_PROD
SELLSY_USER_SECRET_PROD
```

---

## 🚀 Déploiement

### Étape 1 : Configurer les secrets GitHub

1. Va sur **Settings → Secrets and variables → Actions**
2. Clique sur **"New repository secret"**
3. Ajoute les 6 secrets SANDBOX (un par un)

### Étape 2 : Pousser le code sur GitHub

```bash
# Depuis le répertoire du projet
git add .
git commit -m "Add: V2.0 Grilles de remise dynamiques - Sandbox"
git push origin main
```

### Étape 3 : Tester l'exécution manuelle

1. Va sur **Actions** dans ton repo GitHub
2. Sélectionne le workflow **"🧪 Sync Subscription Invoices - SANDBOX"**
3. Clique sur **"Run workflow"**
4. ✅ Coche **"Mode test (ne crée pas réellement les factures)"** pour un premier test
5. Clique sur **"Run workflow"**

### Étape 4 : Vérifier les résultats

**Dans les logs GitHub Actions :**
- ✅ Connexion Airtable établie
- ✅ Grille de remise récupérée
- ✅ Calcul des remises effectué
- ✅ Facture créée dans Sellsy (si dry-run désactivé)

**Dans Sellsy :**
- Vérifie qu'une facture a été créée
- Vérifie que la remise est correcte (20% année 1)

**Dans Airtable :**
- Vérifie que `Mois facturés` = 1
- Vérifie que `Occurrences restantes` a diminué

---

## 🧪 Tests

### Test 1 : Dry-run (mode simulation)

```bash
# Exécution manuelle avec dry-run activé
Actions → Run workflow → Cocher "Mode test"
```

**Résultat attendu :**
- Logs affichent les calculs
- AUCUNE facture créée dans Sellsy
- AUCUNE mise à jour dans Airtable

### Test 2 : Création réelle d'une facture

```bash
# Exécution manuelle SANS dry-run
Actions → Run workflow → Décocher "Mode test"
```

**Résultat attendu :**
- Facture créée dans Sellsy
- Compteurs mis à jour dans Airtable
- Email de notification envoyé au client (via GoCardless)

---

## 📅 Planification automatique

Le workflow s'exécute **automatiquement tous les jours à 9h UTC** (10h FR hiver, 11h FR été).

Pour modifier l'horaire, édite le cron dans `.github/workflows/sync_subscription_invoices_sandbox.yml` :

```yaml
schedule:
  - cron: '0 9 * * *'  # 9h UTC
```

---

## 🔍 Monitoring

### Vérifier les logs

1. Va sur **Actions** dans ton repo
2. Clique sur la dernière exécution
3. Consulte les logs détaillés

### Alertes en cas d'erreur

- GitHub envoie un email automatiquement en cas d'échec
- Les erreurs sont marquées en rouge dans les logs

---

## 🎯 Logique de sélection des grilles

**Ordre de priorité :**

1. **Grille spécifique** liée à l'abonnement (champ `Grille de remise`)
2. **Grille par défaut** active (champ `Grille par défaut` = ✅)
3. **Pas de remise** si aucune grille trouvée

**Exemple :**
```
Client A → Pas de grille spécifique → Grille par défaut (20%/15%/0%)
Client B (VIP) → Grille "VIP Enterprise" (25%/20%/10%)
Client C → Remise décochée → Prix plein (0%/0%/0%)
```

---

## 💡 Cas d'usage

### Créer une nouvelle grille

1. Va dans Airtable → Table `grilles_remise`
2. Clique sur **"+"**
3. Remplis les champs :
   - Nom de la grille
   - Année 1/2/3+ (%)
   - Labels
   - Actif : ✅
   - Grille par défaut : ✅ (si c'est la nouvelle par défaut)

### Changer la grille par défaut

1. Crée la nouvelle grille
2. Coche "Grille par défaut" sur la nouvelle
3. Décoche "Grille par défaut" sur l'ancienne
4. Garde l'ancienne active (pour les clients existants)

### Assigner une grille VIP à un client

1. Va dans `service_sellsy`
2. Ouvre l'abonnement du client
3. Champ `Grille de remise` → Sélectionne "VIP Enterprise"
4. Sauvegarde

---

## 🐛 Dépannage

### Erreur : "Variables d'environnement manquantes"

→ Vérifie que tous les secrets GitHub sont configurés

### Erreur : "Aucune grille par défaut trouvée"

→ Va dans Airtable → `grilles_remise` → Coche "Grille par défaut" sur une grille active

### Facture créée sans remise

→ Vérifie que `Appliquer remise dégressive` est coché sur l'abonnement

---

## 📞 Support

**En cas de problème :**
- Vérifie les logs GitHub Actions
- Vérifie que la grille est `Actif: true`
- Vérifie qu'une grille par défaut existe

---

## 📄 Licence

Usage interne SunLib uniquement.

**Version :** 2.0  
**Date :** Janvier 2026  
**Auteur :** Julien - CTO SunLib
