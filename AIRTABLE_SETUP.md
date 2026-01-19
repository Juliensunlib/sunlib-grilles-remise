# Configuration Airtable - Guide de mise à jour

Ce guide explique comment configurer Airtable pour utiliser le nouveau système de remises avec labels.

## 📋 Table : `grilles_remise`

### Structure des champs

| Nom du champ | Type | Description | Exemple |
|--------------|------|-------------|---------|
| `Nom de la grille` | Texte | Nom descriptif de la grille | "Offre de lancement" |
| `Année 1 (%)` | Nombre | Pourcentage remise année 1 | 100 |
| `Label Année 1` | Texte | Label affiché sur facture | "🎉 Offre de lancement" |
| `Année 2 (%)` | Nombre | Pourcentage remise année 2 | 50 |
| `Label Année 2` | Texte | Label affiché sur facture | "💫 Fidélité Année 2" |
| `Année 3+ (%)` | Nombre | Pourcentage remise année 3+ | 25 |
| `Label Année 3+` | Texte | Label affiché sur facture | "⭐ Ancien client" |
| `Actif` | Checkbox | Si la grille est active | ✅ |
| `Grille par défaut` | Checkbox | Si c'est la grille par défaut | ❌ |

### ⚠️ Important

**Format exact des noms de champs** :
- ✅ `Année 1 (%)` → avec l'espace et les parenthèses
- ❌ `Annee 1 %` → ne fonctionnera pas
- ❌ `an1_pct` → ancien format, ne fonctionne plus

**Labels** :
- Si `Année X (%) > 0`, alors `Label Année X` doit être renseigné
- Si `Année X (%) = 0`, le label peut être vide (la ligne de remise ne sera pas créée)

## 🔧 Migration depuis l'ancien système

Si vous avez l'ancien système avec les champs `an1_pct`, `an1_label`, etc., voici comment migrer :

### Étape 1 : Créer les nouveaux champs

Dans la table `grilles_remise`, ajouter :
1. `Année 1 (%)` - Type : Nombre
2. `Label Année 1` - Type : Texte
3. `Année 2 (%)` - Type : Nombre
4. `Label Année 2` - Type : Texte
5. `Année 3+ (%)` - Type : Nombre
6. `Label Année 3+` - Type : Texte

### Étape 2 : Copier les données

Pour chaque grille existante :
- Copier `an1_pct` → `Année 1 (%)`
- Copier `an1_label` → `Label Année 1`
- Copier `an2_pct` → `Année 2 (%)`
- Copier `an2_label` → `Label Année 2`
- Copier `an3_pct` → `Année 3+ (%)`
- Copier `an3_label` → `Label Année 3+`

### Étape 3 : Vérifier

✅ Tous les pourcentages sont corrects
✅ Tous les labels sont renseignés (sauf si pourcentage = 0)
✅ Au moins une grille a `Actif = ✅`

### Étape 4 : Supprimer les anciens champs (optionnel)

Une fois que tout fonctionne, vous pouvez supprimer :
- `an1_pct`, `an1_label`
- `an2_pct`, `an2_label`
- `an3_pct`, `an3_label`

## 💡 Exemples de grilles

### Grille 1 : Offre de lancement

| Champ | Valeur |
|-------|--------|
| Nom de la grille | Offre de lancement |
| Année 1 (%) | 100 |
| Label Année 1 | 🎉 Offre de lancement |
| Année 2 (%) | 50 |
| Label Année 2 | 💫 Fidélité Année 2 |
| Année 3+ (%) | 25 |
| Label Année 3+ | ⭐ Ancien client |
| Actif | ✅ |
| Grille par défaut | ❌ |

### Grille 2 : Standard (sans remise année 1)

| Champ | Valeur |
|-------|--------|
| Nom de la grille | Standard |
| Année 1 (%) | 0 |
| Label Année 1 | *(vide)* |
| Année 2 (%) | 20 |
| Label Année 2 | 🎁 Fidélité |
| Année 3+ (%) | 10 |
| Label Année 3+ | ⭐ Ancien client |
| Actif | ✅ |
| Grille par défaut | ✅ |

### Grille 3 : Premium

| Champ | Valeur |
|-------|--------|
| Nom de la grille | Premium |
| Année 1 (%) | 50 |
| Label Année 1 | ✨ Bienvenue Premium |
| Année 2 (%) | 30 |
| Label Année 2 | 💎 Premium Année 2 |
| Année 3+ (%) | 15 |
| Label Année 3+ | 🏆 VIP |
| Actif | ✅ |
| Grille par défaut | ❌ |

## 🎨 Suggestions de labels

Voici quelques idées de labels attractifs :

**Année 1 (lancement)** :
- 🎉 Offre de lancement
- ✨ Bienvenue
- 🚀 Nouveau client
- 🎁 Offre découverte
- 💥 Première année offerte

**Année 2 (fidélité)** :
- 💫 Fidélité Année 2
- 🎁 Remise fidélité
- ⭐ Client fidèle
- 💎 Renouvellement
- 🤝 Merci pour votre fidélité

**Année 3+ (ancienneté)** :
- ⭐ Ancien client
- 🏆 VIP
- 💎 Client premium
- 👑 Client historique
- 🌟 Partenaire de longue date

## ✅ Checklist de validation

Avant de lancer le script en production :

- [ ] Tous les champs sont créés avec le bon format
- [ ] Au moins une grille est active (`Actif = ✅`)
- [ ] Une grille par défaut est définie (`Grille par défaut = ✅`)
- [ ] Tous les labels sont renseignés (sauf si pourcentage = 0)
- [ ] Les pourcentages sont cohérents (dégressifs recommandé)
- [ ] Test effectué avec `python3 test_discount_logic.py`
- [ ] Test dry-run effectué avec `DRY_RUN=true python3 sync_subscription_invoices.py`

## 🔗 Table : `service_sellsy` (Abonnements)

Chaque abonnement doit avoir :
- `Grille de remise` → Lien vers une grille de la table `grilles_remise`
- Si le champ est vide, la grille par défaut sera utilisée

## 📞 Support

En cas de problème :
1. Vérifier que les noms de champs sont **exactement** comme indiqué
2. Vérifier que les labels sont renseignés pour les pourcentages > 0
3. Consulter les logs du script pour identifier l'erreur
4. Tester avec `test_discount_logic.py` pour valider la logique

---

**Dernière mise à jour** : 2026-01-19
