# Changelog - Système de Facturation V2.0

## [2.0.1] - 2026-01-19

### ✅ Corrections importantes

#### 1. Système de labels des remises
**Problème** : Les labels n'apparaissaient pas correctement sur les factures Sellsy

**Solution** :
- Remplacement de `calculate_discount()` par `get_discount_info()` qui retourne `(pourcentage, label)`
- Les labels proviennent maintenant directement des champs Airtable : `Label Année 1`, `Label Année 2`, `Label Année 3+`
- Correction des noms de champs Airtable : `'Année 1 (%)'` au lieu de `'an1_pct'`

**Code modifié** :
```python
# Avant
discount_pct = calculate_discount(mois_a_facturer, discount_grid)

# Après
discount_pct, discount_label = get_discount_info(mois_a_facturer, discount_grid)
```

#### 2. Lignes de remise uniquement si remise > 0%
**Problème** : Des lignes de remise avec montant 0€ pouvaient être créées

**Solution** :
- Ajout de condition : ligne de remise créée uniquement si `discount_pct > 0 AND discount_label != ""`
- Si pas de remise applicable, aucune ligne n'est ajoutée

**Code** :
```python
if discount_pct > 0 and discount_label:
    invoice_lines.append({
        'type': 'discount',
        'label': discount_label,
        'unitAmount': -montant_remise
    })
```

### 📊 Tests ajoutés

#### test_discount_logic.py
- Validation du calcul des remises selon le mois
- Vérification des labels par année
- Test "pas de ligne si remise = 0%"

#### test_facture_groupee.py
- Simulation de facture complète avec 4 services
- Différentes grilles de remise
- Validation du total HT/TTC
- Vérification du comportement multi-grilles

### 📝 Documentation

#### README.md enrichi
- Section "Système de remises dégressives" avec exemple détaillé
- Tableau de structure complète d'une grille
- Section "Tests" avec instructions
- Exemples de labels suggérés

### 🔧 Changements techniques

**Fichier : sync_subscription_invoices.py**
- Ligne 76-92 : Nouvelle méthode `get_discount_info()`
- Ligne 340-346 : Ajout condition création ligne remise
- Ligne 510 : Amélioration des logs avec affichage du label

**Noms de champs Airtable** :
- ✅ `Année 1 (%)` (au lieu de `an1_pct`)
- ✅ `Label Année 1` (nouveau)
- ✅ `Année 2 (%)` (au lieu de `an2_pct`)
- ✅ `Label Année 2` (nouveau)
- ✅ `Année 3+ (%)` (au lieu de `an3_pct`)
- ✅ `Label Année 3+` (nouveau)

### 🎯 Impact

**Avant** :
- Labels des remises : ❌ Problématiques
- Lignes vides : ❌ Possibles
- Tests : ❌ Inexistants

**Après** :
- Labels des remises : ✅ Proviennent d'Airtable
- Lignes vides : ✅ Impossible (condition ajoutée)
- Tests : ✅ 2 fichiers de test complets

### 🚀 Mise en production

Pour déployer ces changements :

1. **Vérifier la structure Airtable**
   - Table `grilles_remise` doit avoir les champs : `Année 1 (%)`, `Label Année 1`, etc.
   - Remplir les labels pour toutes les grilles actives

2. **Exécuter les tests**
   ```bash
   python3 test_discount_logic.py
   python3 test_facture_groupee.py
   ```

3. **Test en dry-run**
   ```bash
   DRY_RUN=true python3 sync_subscription_invoices.py
   ```

4. **Déploiement GitHub Actions**
   - Le workflow utilisera automatiquement le nouveau code
   - Tester d'abord avec "Mode test" activé

### ⚠️ Points d'attention

1. **Labels obligatoires** : Si une grille a un pourcentage > 0%, le label correspondant doit être renseigné
2. **Format des champs** : Respecter exactement `Année 1 (%)` avec l'espace et les parenthèses
3. **Compatibilité** : Ces changements sont rétrocompatibles avec les données existantes

---

**Testé par** : Simulation complète
**Validé le** : 2026-01-19
**Status** : ✅ Prêt pour production
