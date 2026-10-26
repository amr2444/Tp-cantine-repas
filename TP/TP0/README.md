# TP0 — Entraîner, évaluer et comparer des modèles

Ce TP (Lab 2.1, séance 3) consiste à compléter un projet Python reproductible qui charge
des données, les découpe en jeu d'entraînement et jeu de test, entraîne plusieurs modèles
et les compare à une baseline, avec une métrique choisie selon le coût des erreurs.

Le même code a été appliqué à deux prototypes, en changeant seulement `monprojet/config.py` :

- **MaintAI** : prédire les pannes de machines à partir de relevés de capteurs
  (classification, métrique : rappel).
- **CantineAI** : prévoir le nombre de repas servis le lendemain dans une cantine scolaire
  (régression sur série temporelle, métrique : MAE).

Les résultats et le choix des modèles sont détaillés dans le dossier `docs/`.