# Étude de conception — MaintAI

Groupe : [noms] · Version : brouillon · Date : 26/10/2026

## 1. Contexte et utilisateurs

Une usine veut anticiper les pannes de ses machines à partir de relevés de capteurs
(température, vibration, charge, heures de fonctionnement).

- **Utilisateur principal** : le responsable de l'équipe de maintenance de l'usine.
- Utilisateurs secondaires : les techniciens de maintenance (qui inspectent les machines
  signalées), le responsable de production (qui subit les arrêts de ligne).

## 2. Problème et décision

- **Décision que l'utilisateur prend avec le système** : choisir les machines à inspecter.
  Le système signale les relevés à risque de panne ; le responsable garde la décision finale.
- **Fréquence** : chaque matin.
- **Coût d'une erreur, et pour qui** :
  - **Panne manquée** (faux négatif) : une ligne de production arrêtée une journée.
    Coût pour l'usine et la production. C'est l'erreur la plus grave.
  - **Fausse alerte** (faux positif) : une heure d'inspection inutile. Coût pour l'équipe
    de maintenance. Trop de fausses alertes font perdre confiance dans le système.

## 3. Approche par sous-problème

| Sous-problème | Approche (règles / ML / DL / LLM / RAG) | Pourquoi pas une approche plus simple |
|---|---|---|
| Prédire si un relevé se termine par une panne | **ML** : classification binaire (régression logistique avec `class_weight="balanced"` retenue) | Des règles à seuils (« si vibration > X ») combinent mal quatre capteurs et doivent être réglées à la main. Pas de deep learning : 5 000 lignes et 4 variables, c'est trop peu et inutile. Pas de LLM : il n'y a pas de texte. |
| Classer les machines à inspecter en priorité | **Règles** : trier les machines signalées par probabilité de panne décroissante | Un simple tri suffit et reste compréhensible par l'équipe. |

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| `data/exemple_pannes.csv` | Données synthétiques fournies pour le cours ; usage pédagogique | 5 000 relevés, 5 colonnes, 17,6 % de pannes | **Non** : relevés de machines, aucune personne concernée |

Colonnes utiles :
- **Cible** : `failure` (1 = panne, 0 = pas de panne).
- **Variables d'entrée** : `temperature_c` (36 à 93 °C), `vibration_mm_s` (0 à 22 mm/s),
  `load_pct` (20 à 100 %), `runtime_hours` (0 à 30 000 h).

Point d'attention : les classes sont déséquilibrées (17,6 % de pannes seulement).

## 5. Métriques, baseline et critères d'acceptation

- **Baseline et son score** : toujours prédire « pas de panne » (classe majoritaire).
  Accuracy **0,824**, rappel **0** : elle ne détecte aucune panne.
- **Métrique principale, et pourquoi** : le **rappel** (part des pannes réelles détectées).
  Une panne manquée coûte une journée d'arrêt, une fausse alerte une heure d'inspection :
  on cherche d'abord à ne pas rater de panne. On suit aussi la précision, pour ne pas
  noyer l'équipe sous les fausses alertes. L'accuracy est trompeuse ici : la baseline
  atteint 82,4 % sans rien détecter.
- **Critère d'acceptation** : rappel **≥ 0,75** et précision **≥ 0,50**, mesurés sur le
  jeu de test (20 % des données, découpage aléatoire stratifié, graine 42, tenu à l'écart
  de l'entraînement).
- **Résultat obtenu** : régression logistique équilibrée, rappel **0,847** et précision
  **0,527**. Critère **atteint**, de justesse pour la précision.

## 6. Architecture prévue

Fonctionnement quotidien, en lot (batch), chaque matin :

1. **Collecte** : récupérer les derniers relevés de capteurs de chaque machine.
2. **Prévision** : charger le modèle entraîné (`models/model.joblib`) et calculer la
   probabilité de panne de chaque machine.
3. **Priorisation** : lister les machines signalées, de la plus à la moins risquée.
4. **Affichage** : présenter la liste au responsable de maintenance, qui choisit les
   inspections.
5. **Suivi** : enregistrer les inspections et les pannes réelles, pour mesurer le rappel
   et la précision en conditions réelles et réentraîner le modèle.

Entraînement : `python -m monprojet.train`, relancé périodiquement avec les nouveaux relevés.

## 7. Choix technologiques

- **Python** avec environnement virtuel (`.venv`) et versions épinglées dans
  `requirements.txt`, pour un projet reproductible.
- **pandas** pour les données, **scikit-learn** pour le prétraitement (Pipeline,
  ColumnTransformer) et les modèles, **joblib** pour sauvegarder le modèle.
- **pytest** pour les tests automatiques.
- Toute la configuration dans `config.py` : aucun chemin ni nom de colonne écrit en dur.
- **Git / GitHub** pour le code et la documentation.
- Plus tard : **MLflow** pour suivre les modèles, **DVC** pour versionner les données.

## 8. Risques, éthique, confidentialité

- **Pannes manquées** : malgré un rappel de 0,847, environ 15 % des pannes passent
  inaperçues. Le système complète la maintenance préventive, il ne la remplace pas.
- **Fausses alertes** : environ une alerte sur deux est fausse (précision 0,527). Si
  l'équipe perd confiance, elle risque d'ignorer les alertes. Il faut suivre ce chiffre.
- **Données synthétiques** : les vrais capteurs seront plus bruités (pannes de capteurs,
  valeurs manquantes). Les performances devront être remesurées sur données réelles.
- **Évolution dans le temps** : nouvelles machines, vieillissement, changement de
  production. Mesures : suivi des performances et réentraînement régulier.
- **Confidentialité** : aucune donnée personnelle, seulement des mesures de machines.
- **Éthique** : le système aide à la décision sans la remplacer. Il ne doit pas servir à
  évaluer les techniciens.

## 9. Limites et hors périmètre

**Limites**
- Un seul découpage aléatoire : les scores dépendent des 1 000 relevés tirés pour le test.
  Une validation croisée donnerait une estimation plus stable.
- Seuil de décision par défaut (0,5), non réglé ; pas de réglage des hyperparamètres.
- Découpage aléatoire : si les relevés sont datés, un découpage chronologique serait plus
  réaliste.
- Quatre variables seulement, une seule usine.

**Hors périmètre**
- Diagnostiquer la cause de la panne ou la pièce défaillante.
- Planifier automatiquement les interventions.
- Prédire la date exacte de la panne (durée de vie restante).
