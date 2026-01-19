# 🚀 Système de Facturation Automatique V2.0 - Grilles Dynamiques

Système automatisé de création de factures d'abonnement mensuelles dans Sellsy avec remises progressives configurables dans Airtable.

## 🎯 Nouveautés V2.0

✅ **Grilles de remise configurables** - Plus besoin de modifier le code !
✅ **Multi-grilles** - VIP, régionales, promotions, test A/B
✅ **Historique** - Traçabilité complète dans Airtable
✅ **Temps réel** - Changements instantanés, pas de redéploiement
✅ **Facturation groupée** - Services avec même client et même date regroupés sur une seule facture

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
