# 📚 Documentation Complète - Système de Facturation Automatique

**Version :** 2.0
**Date :** Janvier 2026
**Auteur :** Julien - CTO SunLib

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Objectif du système](#objectif-du-système)
3. [Architecture technique](#architecture-technique)
4. [Flux de fonctionnement](#flux-de-fonctionnement)
5. [Structure des données Airtable](#structure-des-données-airtable)
6. [Système de remises dégressives](#système-de-remises-dégressives)
7. [Facturation groupée](#facturation-groupée)
8. [Fichiers du projet](#fichiers-du-projet)
9. [Configuration et déploiement](#configuration-et-déploiement)
10. [Utilisation quotidienne](#utilisation-quotidienne)
11. [Résolution de problèmes](#résolution-de-problèmes)

---

## 🎯 Vue d'ensemble

### Qu'est-ce que ce système ?

Ce système automatise **entièrement** la création de factures mensuelles d'abonnement dans Sellsy, avec des remises dégressives configurables via Airtable. Il fonctionne **sans intervention humaine** et gère :

- ✅ La détection automatique des abonnements à facturer
- ✅ Le calcul intelligent des remises selon l'ancienneté
- ✅ Le regroupement des services par client
- ✅ La création des factures dans Sellsy
- ✅ L'envoi automatique par email aux clients
- ✅ La mise à jour des compteurs dans Airtable

### Nouveautés de la V2.0

- **Grilles de remise configurables** : Plus besoin de modifier le code pour changer les remises
- **Multi-grilles** : Possibilité de créer plusieurs grilles (VIP, régionales, promotions, etc.)
- **Historique complet** : Traçabilité dans Airtable
- **Temps réel** : Les changements dans Airtable sont pris en compte immédiatement
- **Facturation groupée** : Services d'un même client regroupés sur une facture unique
- **Labels personnalisés** : Les descriptions des remises proviennent d'Airtable
- **Remise intelligente** : Aucune ligne créée si remise = 0%

---

## 🎯 Objectif du système

### Problème résolu

**Avant** : Création manuelle des factures mensuelles pour chaque abonnement
- ⏱️ Temps perdu chaque mois
- ❌ Risque d'oubli
- ❌ Erreurs de calcul de remise
- ❌ Gestion manuelle des remises dégressives

**Après** : Automatisation complète
- ✅ Zéro intervention manuelle
- ✅ Zéro oubli possible
- ✅ Calculs de remise automatiques et précis
- ✅ Factures envoyées automatiquement par email
- ✅ Prélèvement GoCardless configuré automatiquement

### Qui utilise ce système ?

- **Gestionnaires d'abonnements** : Configuration des services dans Airtable
- **Comptabilité** : Factures créées automatiquement dans Sellsy
- **Clients** : Reçoivent leurs factures par email automatiquement

---

## 🏗️ Architecture technique

### Stack technologique

```
┌─────────────────────────────────────────────────┐
│             AIRTABLE (Base de données)          │
│  • Table service_sellsy (Abonnements)          │
│  • Table grilles_remise (Configuration)        │
└─────────────────┬───────────────────────────────┘
                  │
                  │ Lecture quotidienne (9h UTC)
                  ↓
┌─────────────────────────────────────────────────┐
│         GITHUB ACTIONS (Automatisation)         │
│  • Workflow quotidien                           │
│  • Script Python sync_subscription_invoices.py  │
│  • Calcul des remises                           │
│  • Regroupement par client                      │
└─────────────────┬───────────────────────────────┘
                  │
                  │ Création factures + envoi email
                  ↓
┌─────────────────────────────────────────────────┐
│              SELLSY (Facturation)               │
│  • Création facture (statut: envoyé)           │
│  • Envoi email automatique au client            │
│  • Configuration GoCardless                     │
└─────────────────┬───────────────────────────────┘
                  │
                  │ Mise à jour compteurs
                  ↓
┌─────────────────────────────────────────────────┐
│             AIRTABLE (Mise à jour)              │
│  • Mois facturés +1                             │
│  • Occurrences restantes -1                     │
└─────────────────────────────────────────────────┘
```

### Langages et bibliothèques

- **Python 3.x** : Langage principal
- **requests** : Appels API REST
- **python-dotenv** : Gestion des variables d'environnement
- **GitHub Actions** : Orchestration et planification

---

## 🔄 Flux de fonctionnement

### Étape 1 : Détection des abonnements éligibles

**Chaque jour à 9h UTC**, le système se connecte à Airtable et cherche les abonnements qui répondent à **TOUS** ces critères :

```
✅ Catégorie = "Abonnement"
✅ Occurrences restantes > 0
✅ Date de début renseignée
✅ Nombre de mois écoulés > Nombre de mois facturés
```

**Exemple** :
- Date de début : 2025-01-01
- Date du jour : 2026-01-23
- Mois écoulés : 12
- Mois facturés : 11
- **→ Ce service doit être facturé (mois 12)**

### Étape 2 : Calcul des remises

Pour chaque service éligible :

1. **Calcul du mois à facturer** : `Mois facturés + 1`
2. **Détermination de l'année** :
   - Année 1 : mois 1 à 12
   - Année 2 : mois 13 à 24
   - Année 3+ : mois 25 et plus
3. **Récupération de la grille de remise** :
   - Grille spécifique (champ `Grille de remise`)
   - OU Grille par défaut (si aucune grille spécifique)
4. **Application du pourcentage** selon l'année
5. **Ajout du label personnalisé** depuis Airtable

### Étape 3 : Regroupement par client

Le système regroupe automatiquement les services qui ont :
- **Même ID client Sellsy** (`ID_Sellsy_abonné`)
- **Même date de facturation**

**Résultat** : Une seule facture avec plusieurs lignes au lieu de plusieurs factures.

### Étape 4 : Création de la facture dans Sellsy

Pour chaque groupe de services :

1. **Création de la facture** avec statut `"sent"` (envoyée)
2. **Ajout des lignes** :
   - Ligne de service (prix HT)
   - Ligne de remise (si pourcentage > 0%)
3. **Configuration GoCardless** pour prélèvement automatique
4. **Envoi automatique par email** au client

**Format de la facture** :

```
Client : Example SAS
Date : 2026-01-23

1. Hébergement web (mois 6, année 1)        29.90€ HT
   ↳ 🎉 Offre de lancement (-100%)         -29.90€

2. Domaine .com (mois 6, année 1)           12.00€ HT
   (pas de remise car grille avec 0%)

3. Support Premium (mois 15, année 2)       99.00€ HT
   ↳ 💎 Premium Année 2 (-30%)             -29.70€

4. Backup automatique (mois 27, année 3+)   15.00€ HT
   ↳ ⭐ Ancien client (-25%)                -3.75€
------------------------------------------------
TOTAL HT                                    68.55€
TVA 20%                                     13.71€
TOTAL TTC                                   82.26€
```

### Étape 5 : Mise à jour des compteurs Airtable

Après création réussie de la facture :

```
Mois facturés : +1
Occurrences restantes : -1
```

**Exemple** :
- Avant : Mois facturés = 11, Occurrences restantes = 13
- Après : Mois facturés = 12, Occurrences restantes = 12

---

## 📊 Structure des données Airtable

### Table `service_sellsy` (Abonnements)

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `Nom du service` | Texte | Nom affiché sur la facture | ✅ |
| `Catégorie` | Liste | "Abonnement" pour être traité | ✅ |
| `ID_Sellsy_abonné` | Nombre | ID du client dans Sellsy | ✅ |
| `Date de début` | Date | Date de début de l'abonnement | ✅ |
| `Prix HT` | Nombre | Prix mensuel hors taxes | ✅ |
| `Mois facturés` | Nombre | Nombre de mois déjà facturés | ✅ |
| `Occurrences restantes` | Nombre | Nombre de mois restants | ✅ |
| `Appliquer remise dégressive` | Checkbox | Active/désactive la remise | ✅ |
| `Grille de remise` | Lien | Grille spécifique (optionnel) | ❌ |
| `Code taxe` | Liste | Code TVA (ex: "fr_1" pour 20%) | ✅ |

**Exemple de ligne** :
```
Nom du service : Hébergement WordPress Premium
Catégorie : Abonnement
ID_Sellsy_abonné : 123456
Date de début : 2025-01-01
Prix HT : 49.90
Mois facturés : 3
Occurrences restantes : 9
Appliquer remise dégressive : ✅
Grille de remise : VIP
Code taxe : fr_1
```

### Table `grilles_remise` (Configuration des remises)

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `Nom de la grille` | Texte | Nom descriptif | ✅ |
| `Année 1 (%)` | Nombre | Remise année 1 (0-100) | ✅ |
| `Label Année 1` | Texte | Description sur facture | Si % > 0 |
| `Année 2 (%)` | Nombre | Remise année 2 (0-100) | ✅ |
| `Label Année 2` | Texte | Description sur facture | Si % > 0 |
| `Année 3+ (%)` | Nombre | Remise année 3+ (0-100) | ✅ |
| `Label Année 3+` | Texte | Description sur facture | Si % > 0 |
| `Actif` | Checkbox | Grille active ou non | ✅ |
| `Grille par défaut` | Checkbox | Grille par défaut | ❌ |

**Exemple de grille VIP** :
```
Nom de la grille : VIP
Année 1 (%) : 100
Label Année 1 : 🎉 Offre de lancement VIP
Année 2 (%) : 50
Label Année 2 : 💎 Fidélité VIP Année 2
Année 3+ (%) : 25
Label Année 3+ : ⭐ Client VIP Ancien
Actif : ✅
Grille par défaut : ❌
```

**Exemple de grille standard** :
```
Nom de la grille : Standard
Année 1 (%) : 20
Label Année 1 : 🎁 Bienvenue
Année 2 (%) : 10
Label Année 2 : 💫 Fidélité Année 2
Année 3+ (%) : 5
Label Année 3+ : ⭐ Ancien client
Actif : ✅
Grille par défaut : ✅
```

---

## 💰 Système de remises dégressives

### Logique de sélection des grilles

Le système choisit la grille de remise selon cet ordre de priorité :

1. **Grille spécifique** : Si le champ `Grille de remise` est renseigné sur l'abonnement
2. **Grille par défaut** : Si `Grille par défaut` = ✅ dans la table `grilles_remise`
3. **Pas de remise** : Si aucune grille n'est trouvée

### Calcul de l'année d'abonnement

```python
mois_a_facturer = mois_factures + 1

if mois_a_facturer <= 12:
    annee = 1
    pourcentage = grille["Année 1 (%)"]
    label = grille["Label Année 1"]
elif mois_a_facturer <= 24:
    annee = 2
    pourcentage = grille["Année 2 (%)"]
    label = grille["Label Année 2"]
else:
    annee = 3
    pourcentage = grille["Année 3+ (%)"]
    label = grille["Label Année 3+"]
```

### Exemples de calcul

**Exemple 1 : Mois 5**
- Mois facturés actuels : 4
- Mois à facturer : 5
- Année : 1
- Remise : Année 1 (ex: 100%)
- Label : "🎉 Offre de lancement"

**Exemple 2 : Mois 15**
- Mois facturés actuels : 14
- Mois à facturer : 15
- Année : 2
- Remise : Année 2 (ex: 50%)
- Label : "💎 Fidélité Année 2"

**Exemple 3 : Mois 27**
- Mois facturés actuels : 26
- Mois à facturer : 27
- Année : 3+
- Remise : Année 3+ (ex: 25%)
- Label : "⭐ Ancien client"

### Création de la ligne de remise

**Règle importante** : Si le pourcentage de remise = 0%, aucune ligne de remise n'est créée sur la facture.

```python
if discount_percentage > 0:
    discount_amount = -1 * (base_price * discount_percentage / 100)

    invoice_lines.append({
        "description": label,  # Ex: "🎉 Offre de lancement"
        "unit_amount": discount_amount,  # Ex: -29.90
        "quantity": 1
    })
```

---

## 📦 Facturation groupée

### Principe du regroupement

**Objectif** : Éviter d'envoyer plusieurs factures à un même client le même jour.

**Critères de regroupement** :
1. **Même ID client Sellsy** (`ID_Sellsy_abonné`)
2. **Même date de facturation** (calculée selon date de début + mois facturés)

**Résultat** : Une seule facture avec plusieurs lignes (une par service + remises associées).

### Exemple de regroupement

**Données Airtable** :
```
Service A : Client 123, Date début 2025-01-01, Mois facturés 5
Service B : Client 123, Date début 2025-01-01, Mois facturés 5
Service C : Client 456, Date début 2025-01-01, Mois facturés 5
```

**Résultat dans Sellsy** :
- **Facture 1** : Client 123 (2 lignes : Service A + Service B + leurs remises)
- **Facture 2** : Client 456 (1 ligne : Service C + sa remise)

### Avantages

✅ **Client** : Une seule facture mensuelle au lieu de plusieurs
✅ **Gestion** : Moins de factures à traiter
✅ **Clarté** : Tous les services visibles sur un document unique
✅ **Prélèvement** : Un seul prélèvement GoCardless regroupé

### Exemple de facture groupée

```
FACTURE #2026-001
Client : SunLib SAS
Date : 2026-01-23

Abonnement mensuel - 3 service(s) :

1. Hébergement WordPress Premium             49.90€ HT
   ↳ 🎉 Offre de lancement (-100%)          -49.90€

2. Nom de domaine .fr                        12.00€ HT
   ↳ 🎁 Bienvenue (-20%)                     -2.40€

3. Support technique 24/7                    99.00€ HT
   ↳ 🎉 Offre de lancement (-100%)          -99.00€
-----------------------------------------------------
TOTAL HT                                      9.60€
TVA 20%                                       1.92€
TOTAL TTC                                    11.52€

Prélèvement GoCardless : Le 05/02/2026
```

---

## 📁 Fichiers du projet

### Fichiers principaux

#### `sync_subscription_invoices.py`
**Rôle** : Orchestrateur principal du système

**Fonctions principales** :
- `get_eligible_subscriptions_for_today()` : Récupère les abonnements à facturer
- `calculate_discount()` : Calcule la remise selon l'année
- `group_services_by_client_and_date()` : Regroupe les services par client
- `create_invoice_for_group()` : Crée la facture dans Sellsy
- `main()` : Point d'entrée principal

**Variables d'environnement utilisées** :
```
AIRTABLE_API_KEY
AIRTABLE_BASE_ID
AIRTABLE_TABLE_NAME
AIRTABLE_GRILLES_TABLE_NAME
SELLSY_API_KEY
SELLSY_API_SECRET
DRY_RUN (optionnel)
```

#### `src/airtable_client.py`
**Rôle** : Client API Airtable

**Méthodes principales** :
- `get_eligible_subscriptions()` : Récupère les abonnements éligibles
- `get_discount_grids()` : Récupère toutes les grilles de remise
- `get_discount_grid(grid_id)` : Récupère une grille spécifique
- `update_service_counters()` : Met à jour les compteurs après facturation

**Exemple d'utilisation** :
```python
client = AirtableClient(
    api_key=os.getenv('AIRTABLE_API_KEY'),
    base_id=os.getenv('AIRTABLE_BASE_ID'),
    table_services='service_sellsy',
    table_grilles='grilles_remise'
)

services = client.get_eligible_subscriptions()
grilles = client.get_discount_grids()
```

#### `src/sellsy_client_v2.py`
**Rôle** : Client API Sellsy pour création de factures

**Méthodes principales** :
- `create_invoice()` : Crée une facture dans Sellsy
- `send_invoice_by_email()` : Envoie la facture par email au client
- `get_invoice_details()` : Récupère les détails d'une facture

**Exemple d'utilisation** :
```python
client = SellsyClient(api_key, api_secret)

invoice_data = {
    "third_id": 123456,
    "subject": "Abonnement mensuel - Janvier 2026",
    "invoice_lines": [
        {
            "description": "Hébergement WordPress",
            "unit_amount": 49.90,
            "quantity": 1,
            "tax_code": "fr_1"
        }
    ]
}

invoice = client.create_invoice(invoice_data, dry_run=False)
client.send_invoice_by_email(invoice['id'])
```

### Fichiers utilitaires

| Fichier | Description | Utilisation |
|---------|-------------|-------------|
| `list_invoices.py` | Liste les factures Sellsy | `python list_invoices.py` |
| `search_invoice.py` | Recherche une facture | `python search_invoice.py` |
| `inspect_invoice.py` | Détails d'une facture | `python inspect_invoice.py <ID>` |
| `get_gocardless_id.py` | Récupère l'ID GoCardless | `python get_gocardless_id.py` |
| `test_grouping.py` | Test du regroupement | `python test_grouping.py` |

### Fichiers de configuration

| Fichier | Description |
|---------|-------------|
| `.env` | Variables d'environnement (local) |
| `requirements.txt` | Dépendances Python |
| `config.py` | Configuration globale |
| `.github/workflows/sync_subscription_invoices_sandbox.yml` | Workflow GitHub Actions |

---

## ⚙️ Configuration et déploiement

### Prérequis

1. **Compte Airtable** avec :
   - Table `service_sellsy` configurée
   - Table `grilles_remise` configurée
   - API Key générée

2. **Compte Sellsy** avec :
   - API Key et Secret
   - Accès API activé

3. **Compte GitHub** avec :
   - Repository du projet
   - GitHub Actions activé

### Configuration des secrets GitHub

**Actions → Settings → Secrets → New repository secret**

Secrets à configurer :
```
AIRTABLE_API_KEY=pat_XXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
AIRTABLE_TABLE_NAME=service_sellsy
AIRTABLE_GRILLES_TABLE_NAME=grilles_remise
SELLSY_API_KEY=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
SELLSY_API_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Configuration du workflow GitHub Actions

**Fichier** : `.github/workflows/sync_subscription_invoices_sandbox.yml`

**Planification actuelle** :
```yaml
schedule:
  - cron: '0 9 * * *'  # Tous les jours à 9h UTC
```

**Déclenchers** :
- Automatique : Tous les jours à 9h UTC
- Manuel : Via l'interface GitHub Actions

**Options du workflow manuel** :
- ✅ Mode test (DRY-RUN) : Simulation sans création réelle

### Installation locale

```bash
# Clone du repository
git clone <url-du-repo>
cd <nom-du-repo>

# Installation des dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# Test de connexion
python src/airtable_client.py

# Exécution en mode test
DRY_RUN=true python sync_subscription_invoices.py

# Exécution réelle
python sync_subscription_invoices.py
```

---

## 🎮 Utilisation quotidienne

### Pour les gestionnaires d'abonnements

#### Ajouter un nouvel abonnement

1. **Ouvrir Airtable** → Table `service_sellsy`
2. **Cliquer sur "+"** pour ajouter un record
3. **Remplir les champs** :
   ```
   Nom du service : Hébergement WordPress
   Catégorie : Abonnement
   ID_Sellsy_abonné : 123456
   Date de début : 2026-01-23
   Prix HT : 49.90
   Mois facturés : 0
   Occurrences restantes : 12
   Appliquer remise dégressive : ✅
   Code taxe : fr_1
   ```
4. **Sauvegarder**

**Résultat** : Le système facturera automatiquement cet abonnement le 23 de chaque mois.

#### Créer une nouvelle grille de remise

1. **Ouvrir Airtable** → Table `grilles_remise`
2. **Cliquer sur "+"**
3. **Remplir** :
   ```
   Nom de la grille : Promotion Hiver
   Année 1 (%) : 50
   Label Année 1 : ❄️ Promo Hiver
   Année 2 (%) : 25
   Label Année 2 : 🎁 Fidélité
   Année 3+ (%) : 10
   Label Année 3+ : ⭐ Ancien client
   Actif : ✅
   Grille par défaut : ❌
   ```
4. **Sauvegarder**

#### Assigner une grille à un abonnement

1. **Ouvrir Airtable** → Table `service_sellsy`
2. **Ouvrir l'abonnement**
3. **Champ `Grille de remise`** → Sélectionner "Promotion Hiver"
4. **Sauvegarder**

**Résultat** : Cet abonnement utilisera la grille "Promotion Hiver" au lieu de la grille par défaut.

#### Changer la grille par défaut

1. **Table `grilles_remise`**
2. **Nouvelle grille** : Cocher `Grille par défaut` = ✅
3. **Ancienne grille** : Décocher `Grille par défaut` = ❌

**Important** : Une seule grille peut être "par défaut" à la fois.

### Pour la comptabilité

#### Vérifier les factures créées

1. **Se connecter à Sellsy**
2. **Facturation → Factures**
3. **Filtrer** : Date du jour, Statut = "Envoyé"

**Résultat** : Liste de toutes les factures créées automatiquement ce matin.

#### Vérifier l'envoi des emails

1. **Ouvrir une facture dans Sellsy**
2. **Onglet "Historique"**
3. **Vérifier** : "Email envoyé le [date]"

#### Vérifier les prélèvements GoCardless

1. **Se connecter à GoCardless**
2. **Paiements → À venir**
3. **Vérifier** : Les montants correspondent aux factures

### Pour le suivi

#### Logs GitHub Actions

1. **GitHub** → **Actions**
2. **Cliquer sur le dernier workflow**
3. **Lire les logs** :
   ```
   ✅ 3 abonnement(s) éligible(s) trouvé(s)
   ✅ 2 grille(s) de remise chargée(s)
   ✅ Facture créée pour Client 123 (2 services)
   ✅ Email envoyé au client
   ✅ Compteurs mis à jour dans Airtable
   ```

#### Vérification dans Airtable

Après exécution du workflow :
- `Mois facturés` doit avoir augmenté de +1
- `Occurrences restantes` doit avoir diminué de -1

**Exemple** :
- Avant : Mois facturés = 5, Occurrences restantes = 7
- Après : Mois facturés = 6, Occurrences restantes = 6

---

## 🔧 Résolution de problèmes

### Problème : Aucune facture créée

**Vérifications** :

1. **Critères d'éligibilité** :
   ```
   ✅ Catégorie = "Abonnement" ?
   ✅ Occurrences restantes > 0 ?
   ✅ Date de début renseignée ?
   ✅ Mois écoulés > Mois facturés ?
   ```

2. **Date anniversaire** :
   - Date de début : 2025-01-15
   - Facturation : Le 15 de chaque mois
   - Si on est le 16 : **Pas de facturation** (trop tard, ce sera le mois prochain)

3. **Logs GitHub Actions** :
   - Vérifier le message : "X abonnement(s) éligible(s) trouvé(s)"
   - Si 0 → Aucun abonnement ne remplit les critères

### Problème : Facture créée sans remise

**Causes possibles** :

1. **Case décochée** : `Appliquer remise dégressive` = ❌
   - **Solution** : Cocher la case dans Airtable

2. **Aucune grille trouvée** :
   - Pas de grille spécifique assignée
   - Pas de grille par défaut active
   - **Solution** : Créer une grille par défaut

3. **Remise = 0%** :
   - La grille a 0% pour cette année
   - **Normal** : Aucune ligne de remise n'est ajoutée

### Problème : Erreur "Aucune grille par défaut trouvée"

**Solution** :

1. **Airtable** → Table `grilles_remise`
2. **Choisir une grille**
3. **Cocher** : `Grille par défaut` = ✅
4. **Vérifier** : `Actif` = ✅

### Problème : Facture créée mais email non envoyé

**Vérifications** :

1. **Email du client** : Vérifier dans Sellsy que l'email est renseigné
2. **Paramètres Sellsy** : Vérifier que l'envoi d'email est activé
3. **Logs GitHub** : Chercher le message "Email envoyé au client"

**Solution temporaire** :
- Envoyer manuellement depuis Sellsy (bouton "Envoyer par email")

### Problème : Prélèvement GoCardless non configuré

**Vérification** :

```bash
python get_gocardless_id.py
```

**Si aucun ID retourné** :
1. Vérifier la connexion GoCardless dans Sellsy
2. Vérifier que le client a un mandat GoCardless actif

### Problème : Variables d'environnement manquantes

**Erreur** :
```
ValueError: AIRTABLE_API_KEY is not set
```

**Solution GitHub Actions** :
1. **Settings → Secrets**
2. **Vérifier** : Tous les secrets sont configurés
3. **Ajouter** : Le secret manquant

**Solution locale** :
1. **Copier** : `.env.example` → `.env`
2. **Éditer** : Remplir toutes les clés API
3. **Vérifier** : `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('AIRTABLE_API_KEY'))"`

### Problème : Compteurs non mis à jour

**Causes possibles** :

1. **Erreur après création** : La facture a été créée mais une erreur est survenue ensuite
2. **Mode test activé** : `DRY_RUN=true` → Aucune mise à jour réelle

**Solution** :
1. **Vérifier les logs** : Chercher "Mise à jour des compteurs"
2. **Mise à jour manuelle** :
   - Ouvrir l'abonnement dans Airtable
   - `Mois facturés` : +1
   - `Occurrences restantes` : -1

### Problème : Factures en double

**Cause** : Le workflow a été exécuté plusieurs fois le même jour

**Solution immédiate** :
1. **Supprimer** les factures en double dans Sellsy
2. **Remettre les compteurs** dans Airtable

**Prévention** :
- Ne pas exécuter manuellement le workflow si l'automatique a déjà tourné
- Toujours vérifier les logs avant de relancer

### Problème : Erreur API Sellsy

**Erreurs courantes** :

1. **401 Unauthorized** :
   - Clés API incorrectes
   - **Solution** : Régénérer les clés dans Sellsy

2. **429 Too Many Requests** :
   - Trop de requêtes
   - **Solution** : Attendre 1 minute et relancer

3. **500 Internal Server Error** :
   - Problème côté Sellsy
   - **Solution** : Attendre et réessayer plus tard

### Problème : Erreur API Airtable

**Erreurs courantes** :

1. **401 Unauthorized** :
   - API Key incorrecte
   - **Solution** : Régénérer l'API Key dans Airtable

2. **404 Not Found** :
   - Base ID ou Table name incorrect
   - **Solution** : Vérifier les identifiants dans `.env`

3. **422 Invalid Request** :
   - Champ manquant ou invalide
   - **Solution** : Vérifier la structure de la table

---

## 📊 Bonnes pratiques

### Gestion des grilles de remise

✅ **Créer des grilles avec des noms explicites** :
- ❌ Mauvais : "Grille 1", "Test", "Nouvelle"
- ✅ Bon : "VIP 2026", "Promo Hiver", "Standard"

✅ **Toujours avoir une grille par défaut active**

✅ **Désactiver les anciennes grilles** au lieu de les supprimer (historique)

✅ **Tester une nouvelle grille** :
1. Créer la grille (Actif = ✅, Par défaut = ❌)
2. L'assigner à UN seul abonnement test
3. Exécuter le workflow en mode DRY-RUN
4. Si OK, l'utiliser plus largement

### Gestion des abonnements

✅ **Utiliser des noms de service clairs et descriptifs**

✅ **Vérifier la date de début** : C'est elle qui détermine la date de facturation mensuelle

✅ **Configurer les occurrences** : 12 pour un an, 24 pour 2 ans, 999 pour illimité

✅ **Ne jamais modifier manuellement** `Mois facturés` (sauf correction d'erreur)

### Monitoring

✅ **Vérifier les logs chaque jour** après l'exécution automatique

✅ **Créer des alertes** si le workflow échoue (GitHub Actions notifications)

✅ **Faire un test mensuel** : Exécuter manuellement en mode DRY-RUN pour vérifier

### Sécurité

✅ **Ne jamais committer les clés API** dans le code

✅ **Utiliser les secrets GitHub** pour toutes les variables sensibles

✅ **Régénérer les clés API** périodiquement (tous les 6 mois)

✅ **Limiter les accès** : Seules les personnes autorisées doivent avoir accès aux secrets

---

## 📈 Évolutions futures possibles

### Fonctionnalités potentielles

- **Notifications Slack/Email** après chaque exécution
- **Dashboard de suivi** : Statistiques sur les facturations
- **Gestion des impayés** : Alerte si GoCardless échoue
- **Export comptable** : Export automatique vers logiciel comptable
- **Multi-devises** : Support de plusieurs devises
- **Remises personnalisées** : Remises calculées selon d'autres critères (CA, volume, etc.)

### Améliorations techniques

- **Tests unitaires** : Coverage à 100%
- **Logs structurés** : Format JSON pour meilleure analyse
- **Retry automatique** : En cas d'erreur API temporaire
- **Webhooks** : Notifications en temps réel
- **Interface web** : Dashboard de gestion (optionnel)

---

## 📝 Glossaire

| Terme | Définition |
|-------|------------|
| **Abonnement** | Service facturé mensuellement de manière récurrente |
| **Mois facturés** | Nombre de mois déjà facturés depuis le début |
| **Occurrences restantes** | Nombre de mois restants à facturer |
| **Grille de remise** | Configuration des pourcentages de remise par année |
| **Année d'abonnement** | Période de 12 mois (Année 1 = mois 1-12, Année 2 = mois 13-24, etc.) |
| **DRY-RUN** | Mode test qui simule l'exécution sans créer réellement les factures |
| **GoCardless** | Service de prélèvement bancaire automatique |
| **Facturation groupée** | Regroupement de plusieurs services sur une seule facture |
| **Label de remise** | Description personnalisée de la remise affichée sur la facture |

---

## 🆘 Support et contact

### En cas de problème

1. **Vérifier cette documentation** en premier
2. **Consulter les logs GitHub Actions**
3. **Tester en mode DRY-RUN** pour identifier le problème
4. **Contacter le support technique**

### Ressources

- **Documentation Airtable API** : https://airtable.com/developers/web/api/introduction
- **Documentation Sellsy API** : https://api.sellsy.com/doc/v2/
- **Documentation GitHub Actions** : https://docs.github.com/en/actions

---

**Version :** 2.0
**Dernière mise à jour :** Janvier 2026
**Auteur :** Julien - CTO SunLib

---

*Cette documentation couvre l'intégralité du système de facturation automatique. Pour toute question ou suggestion d'amélioration, n'hésitez pas à nous contacter.*
