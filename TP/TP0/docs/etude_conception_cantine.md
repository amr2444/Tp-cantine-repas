# Étude de conception — CantineAI

Groupe : EL BELLAOUI Amr , BENLAAMA Issam · Version : brouillon · Date : 26/10/2026

## 1. Contexte et utilisateurs

La cantine d'un lycée sert le déjeuner du lundi au vendredi à environ 650 élèves inscrits.
Chaque jour, la quantité de repas commandée à la cuisine est estimée « à la main ».

- **Utilisateur principal** : le gestionnaire de la cantine du lycée.
- Utilisateurs secondaires : l'équipe de cuisine (qui prépare les repas commandés),
  l'intendance (qui suit les coûts et le gaspillage).

## 2. Problème et décision

- **Décision que l'utilisateur prend avec le système** : le nombre de repas du lendemain
  à commander à la cuisine. Le système propose une prévision ; le gestionnaire garde la
  décision finale.
- **Fréquence** : une fois par jour d'école, à 10 h, pour le lendemain.
- **Coût d'une erreur, et pour qui** :
  - **Trop de repas** : environ 15 DH de matière première perdus par repas en trop, et du
    gaspillage alimentaire. Coût pour la cantine et l'intendance.
  - **Pas assez de repas** : un élève sans déjeuner, ou un sandwich de remplacement acheté
    en urgence, et des plaintes des parents. Coût pour les élèves et pour le gestionnaire.
    Cette erreur est jugée plus grave que la précédente.

## 3. Approche par sous-problème

| Sous-problème | Approche (règles / ML / DL / LLM / RAG) | Pourquoi pas une approche plus simple |
|---|---|---|
| Prévoir le nombre de repas du lendemain | **ML** : régression (régression linéaire retenue) sur données tabulaires | La règle actuelle (« même jour, semaine précédente ») ignore le menu, la météo, les examens et les sorties : elle fait moins bien que la simple moyenne (MAE 76,0 contre 70,3). Pas de deep learning : 340 lignes, c'est trop peu. Pas de LLM : il n'y a pas de texte. |
| Se protéger contre le manque de repas | **Règles** : ajouter une marge de sécurité à la prévision (à fixer à partir des erreurs observées) | Une simple règle suffit, transparente et facile à régler par le gestionnaire. |
| Rassembler les informations du lendemain (menu, météo prévue, calendrier) | **Règles** : lecture du planning des menus, du calendrier scolaire et d'une prévision météo | Ce sont des informations connues à l'avance ; aucun apprentissage n'est nécessaire. |

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| `data/cantine_repas.csv` | Données synthétiques générées pour le cours, fournies par l'enseignant ; usage pédagogique | 340 jours d'école (09/09/2024 → 19/06/2026), une ligne par jour, 11 colonnes | **Non** : uniquement des totaux par jour, aucun élève identifiable |

Colonnes utiles :
- **Cible** : `repas_servis` (250 à 700).
- **Variables d'entrée** : `jour`, `inscrits`, `menu`, `temperature_c`, `pluie_mm`, `examens`,
  `sortie_scolaire`, `veille_vacances`, `repas_semaine_precedente`.
- `date` sert uniquement au découpage chronologique ; elle n'est pas donnée au modèle.

Points d'attention :
- `repas_semaine_precedente` est vide après des vacances (10 jours sur les 68 du test).
- En production, la météo sera une **prévision** de la veille, avec sa propre erreur.

## 5. Métriques, baseline et critères d'acceptation

- **Baseline et son score** : la méthode actuelle du gestionnaire, qui reprend le nombre de
  repas du même jour la semaine précédente. **MAE = 76,0 repas** sur le jeu de test
  (les jours sans valeur, après les vacances, sont remplacés par la moyenne de
  l'entraînement). Pour référence, « toujours prédire la moyenne » obtient une MAE de 70,3.
- **Métrique principale, et pourquoi** : la **MAE en nombre de repas**. Elle se lit
  directement (« on se trompe en moyenne de N repas par jour ») et chaque repas d'écart a
  un coût concret : environ 15 DH s'il est en trop, un élève sans déjeuner s'il manque.
  On suit aussi la RMSE (qui pénalise davantage les grosses erreurs) et le R².
- **Critère d'acceptation** : MAE **au moins 15 % sous** celle de la baseline
  « semaine précédente », mesurée sur les **68 jours les plus récents** (20 % des données,
  découpage chronologique : entraînement sur le passé, test sur le futur).
- **Résultat obtenu** : régression linéaire, **MAE = 22,2 repas**, soit **70,7 % sous la
  baseline métier**. Critère **atteint**.

## 6. Architecture prévue

Fonctionnement quotidien, en lot (batch), chaque jour d'école à 10 h :

1. **Collecte** : récupérer les informations du lendemain (menu, prévision météo,
   calendrier des examens et sorties, nombre d'inscrits, repas servis la semaine précédente).
2. **Prévision** : charger le modèle entraîné (`models/model.joblib`) et prédire le nombre
   de repas.
3. **Ajustement** : ajouter la marge de sécurité (règle).
4. **Affichage** : présenter au gestionnaire la prévision, la marge et les facteurs
   principaux (examens, sortie, menu…). Il valide ou corrige.
5. **Suivi** : enregistrer chaque jour la prévision et le nombre réellement servi, pour
   mesurer l'erreur et réentraîner le modèle régulièrement.

Entraînement : `python -m monprojet.train`, relancé périodiquement avec les nouveaux jours.

## 7. Choix technologiques

- **Python** avec environnement virtuel (`.venv`) et versions épinglées dans
  `requirements.txt`, pour un projet reproductible.
- **pandas** pour les données, **scikit-learn** pour le prétraitement (Pipeline,
  ColumnTransformer) et les modèles, **joblib** pour sauvegarder le modèle.
- **pytest** pour les tests automatiques.
- Toute la configuration dans `config.py` : aucun chemin ni nom de colonne écrit en dur.
- **Git / GitHub** pour le code et la documentation du groupe.
- Plus tard : **MLflow** pour suivre les modèles, **DVC** pour versionner les données.
- Interface pour le gestionnaire (API ou petite application web) : à choisir dans les
  prochaines séances.

## 8. Risques, éthique, confidentialité

- **Sous-estimation** : un élève sans repas est l'erreur la plus grave. Mesures : marge de
  sécurité, et décision finale laissée au gestionnaire.
- **Données synthétiques** : les vraies données seront plus bruitées (absences, grèves,
  épidémies). Les performances réelles seront probablement moins bonnes ; il faudra les
  remesurer.
- **Évolution dans le temps** : nouveaux menus, changement du nombre d'inscrits, nouveau
  calendrier. Mesures : suivi de l'erreur quotidienne, réentraînement régulier.
- **Erreur de la prévision météo** : le modèle dépend d'une prévision, pas de la météo
  réelle.
- **Événements imprévus** (grève, fermeture exceptionnelle) : hors de portée du modèle ;
  le gestionnaire doit pouvoir corriger à la main.
- **Confidentialité** : aucune donnée personnelle, seulement des totaux par jour. Si l'on
  ajoutait plus tard des données par élève (présences, régimes), il faudrait respecter la
  loi 09-08 sur la protection des données personnelles et limiter les données au strict
  nécessaire.
- **Éthique** : le système aide à la décision sans la remplacer ; l'objectif est de réduire
  le gaspillage sans priver d'élève de repas.

## 9. Limites et hors périmètre

**Limites**
- 340 jours seulement, dont 68 de test : le score dépend de la période testée (fin d'année
  scolaire, avec examens).
- La MAE traite de la même façon un repas en trop et un repas manquant, alors que le
  second est plus grave.
- Pas de réglage des hyperparamètres ni de validation sur plusieurs périodes.

**Hors périmètre**
- Prévoir les quantités par ingrédient ou par plat.
- Passer automatiquement la commande à la cuisine.
- Prévoir les repas du soir, des week-ends ou des vacances.
- Prévoir la présence de chaque élève individuellement.