# 🚀 Système de Facturation Automatique V2.0 - Grilles Dynamiques

Système automatisé de création de factures d'abonnement mensuelles dans Sellsy avec remises progressives configurables dans Airtable.

## 🎯 Nouveautés V2.0

✅ **Grilles de remise configurables** - Plus besoin de modifier le code !
✅ **Multi-grilles** - VIP, régionales, promotions, test A/B
✅ **Historique** - Traçabilité complète dans Airtable
✅ **Temps réel** - Changements instantanés, pas de redéploiement
✅ **Facturation groupée** - Services avec même client et même date regroupés sur une seule facture
✅ **Labels personnalisés** - Les labels des remises proviennent directement d'Airtable
✅ **Remise intelligente** - Aucune ligne créée si remise = 0%

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
    ↓ Création facture avec remise (statut: draft)
    ↓ Envoi manuel depuis Sellsy → Prélèvement GoCardless auto
AIRTABLE
    ↓ Mise à jour compteurs (Mois facturés +1, Occurrences restantes -1)
```

---

## ⚠️ Limitations API Sellsy

**Envoi automatique par email** : L'API Sellsy v2 ne permet pas d'envoyer automatiquement les factures par email. Le script crée les factures en statut "draft" dans Sellsy.

**Action requise** : Après l'exécution du script, vous devez :
1. Vous connecter à votre interface Sellsy
2. Consulter les factures créées (lien public fourni dans les logs)
3. Les envoyer manuellement par email aux clients

**Alternative** : Configurez un workflow manuel ou utilisez les fonctionnalités d'automatisation de Sellsy pour l'envoi groupé de factures.

---

## 🚀 Test rapide (DRY-RUN)

### Première exécution - Mode simulation

1. Va sur **Actions** dans ton repo
2. Clique sur **"🧪 Sync Subscription Invoices - SANDBOX"**
3. Clique sur **"Run workflow"**
4. ✅ **Coche "Mode test (ne crée pas réellement les factures)"**
5. Clique sur **"Run workflow"**

**Résultat attendu :**
- ✅ Logs affichent les calculs de remise
- ✅ Aucune facture créée dans Sellsy
- ✅ Aucune mise à jour dans Airtable

---

## 🎯 Test réel (création facture)

### Une fois le dry-run validé

1. **Actions → Run workflow**
2. ❌ **Décoche "Mode test"**
3. Clique sur **"Run workflow"**

**Résultat attendu :**
- ✅ Facture créée dans Sellsy avec remise 20%
- ✅ Compteurs mis à jour dans Airtable

---

## 📅 Planification automatique

Le workflow s'exécute **automatiquement tous les jours à 9h UTC** (10h FR hiver, 11h FR été).

Pour le désactiver temporairement, commente le cron dans le workflow :
```yaml
# schedule:
#   - cron: '0 9 * * *'
```

---

## 💰 Système de remises dégressives

### Comment ça fonctionne

Pour chaque service à facturer, le système :

1. **Calcule le mois à facturer** : `mois_ecoules + 1` depuis la date de début
2. **Détermine l'année en cours** :
   - Année 1 : mois 1 à 12
   - Année 2 : mois 13 à 24
   - Année 3+ : mois 25 et plus
3. **Récupère la remise applicable** depuis la grille Airtable
4. **Crée une ligne de remise** uniquement si le pourcentage > 0%

### Structure d'une grille de remise

Chaque grille contient 6 champs dans Airtable :

| Champ | Type | Exemple |
|-------|------|---------|
| `Année 1 (%)` | Nombre | 100 |
| `Label Année 1` | Texte | 🎉 Offre de lancement |
| `Année 2 (%)` | Nombre | 50 |
| `Label Année 2` | Texte | 💫 Fidélité Année 2 |
| `Année 3+ (%)` | Nombre | 25 |
| `Label Année 3+` | Texte | ⭐ Ancien client |

### Exemple de facture avec remises

```
Client : Example SAS
Date : 2026-01-19

1. Hébergement web (mois 6, année 1)        29.90€ HT
   ↳ 🎉 Offre de lancement (-100%)         -29.90€

2. Domaine .com (mois 6, année 1)           12.00€ HT
   (pas de remise - grille avec 0% an 1)

3. Support Premium (mois 15, année 2)       99.00€ HT
   ↳ 💎 Premium Année 2 (-30%)             -29.70€

4. Backup automatique (mois 27, année 3+)   15.00€ HT
   ↳ ⭐ Ancien client (-25%)                -3.75€
------------------------------------------------
TOTAL HT                                    68.55€
TVA 20%                                     13.71€
TOTAL TTC                                   82.26€
```

**Points importants** :
- Chaque service peut avoir sa propre grille de remise
- Le label affiché provient directement d'Airtable
- Si `Année X (%)` = 0, aucune ligne de remise n'est créée
- La remise s'applique sur le prix HT de chaque ligne

---

## 🎯 Logique de sélection des grilles

**Ordre de priorité :**

1. **Grille spécifique** liée à l'abonnement (champ `Grille de remise`)
2. **Grille par défaut** active (champ `Grille par défaut` = ✅)
3. **Pas de remise** si aucune grille trouvée

---

## 💡 Gestion des grilles dans Airtable

### Créer une nouvelle grille

1. Airtable → Table `grilles_remise`
2. Clique sur **"+"**
3. Remplis :
   - Nom de la grille
   - Année 1/2/3+ (%)
   - Labels
   - Actif : ✅
   - Grille par défaut : ✅ (si applicable)

### Changer la grille par défaut

1. Crée la nouvelle grille
2. Coche "Grille par défaut" sur la nouvelle
3. Décoche "Grille par défaut" sur l'ancienne

### Structure complète d'une grille

| Champ Airtable | Type | Description | Obligatoire |
|----------------|------|-------------|-------------|
| `Nom de la grille` | Texte | Nom descriptif | ✅ |
| `Année 1 (%)` | Nombre | Remise année 1 (0-100) | ✅ |
| `Label Année 1` | Texte | Label facture année 1 | Si % > 0 |
| `Année 2 (%)` | Nombre | Remise année 2 (0-100) | ✅ |
| `Label Année 2` | Texte | Label facture année 2 | Si % > 0 |
| `Année 3+ (%)` | Nombre | Remise année 3+ (0-100) | ✅ |
| `Label Année 3+` | Texte | Label facture année 3+ | Si % > 0 |
| `Actif` | Checkbox | Grille active | ✅ |
| `Grille par défaut` | Checkbox | Grille par défaut | ❌ |

**Exemples de labels** :
- 🎉 Offre de lancement
- 💫 Fidélité Année 2
- ⭐ Ancien client
- 🎁 Remise fidélité
- 💎 Client Premium

### Assigner une grille à un abonnement

1. Table `service_sellsy`
2. Ouvre l'abonnement
3. Champ `Grille de remise` → Sélectionne la grille
4. Sauvegarde

---

## 📦 Facturation groupée

### Principe

Lorsque plusieurs services Airtable ont :
- **Le même ID client Sellsy** (`ID_Sellsy_abonné`)
- **La même date de facturation** (calculée selon date de début + mois facturés)

→ Ils sont automatiquement regroupés sur **une seule facture** avec plusieurs lignes.

### Avantages

✅ **Client** : Une seule facture mensuelle au lieu de plusieurs
✅ **Gestion** : Moins de factures à traiter
✅ **Clarté** : Tous les services visibles sur un document unique

### Exemple

**Airtable** :
- Service A : Client 123, Date début 2025-01-01, Mois facturés 0
- Service B : Client 123, Date début 2025-01-01, Mois facturés 0
- Service C : Client 456, Date début 2025-01-01, Mois facturés 0

**Résultat dans Sellsy** :
- Facture 1 : Client 123 (2 lignes : Service A + Service B)
- Facture 2 : Client 456 (1 ligne : Service C)

### Comportement

- Chaque ligne conserve sa remise individuelle selon sa grille
- Le sujet de la facture indique le nombre de services groupés
- Tous les compteurs Airtable sont mis à jour après création

---

## 🧪 Tests

Le projet inclut des tests pour valider la logique métier :

### Test de la logique des remises
```bash
python3 test_discount_logic.py
```

Valide :
- Calcul correct des remises selon le mois
- Application des bons labels selon l'année
- Aucune ligne créée si remise = 0%

### Test de facture groupée
```bash
python3 test_facture_groupee.py
```

Simule une facture complète avec :
- Plusieurs services
- Différentes grilles de remise
- Différentes années d'abonnement
- Calcul du total HT/TTC

Ces tests ne nécessitent aucune connexion API et peuvent être exécutés à tout moment.

---

## 🐛 Dépannage

### Erreur : "Variables d'environnement manquantes"
→ Vérifie que tous les secrets GitHub sont configurés

### Erreur : "Aucune grille par défaut trouvée"
→ Airtable → `grilles_remise` → Coche "Grille par défaut" sur une grille active

### Facture créée sans remise
→ Vérifie que `Appliquer remise dégressive` est coché sur l'abonnement

---

## 📞 Support

En cas de problème :
- Vérifie les logs GitHub Actions
- Vérifie que la grille est `Actif: true`
- Vérifie qu'une grille par défaut existe

---

**Version :** 2.0  
**Date :** Janvier 2026  
**Auteur :** Julien - CTO SunLib
