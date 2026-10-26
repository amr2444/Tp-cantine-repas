# ADR 002 : Validation des relevés et comportement sans modèle

Date : 26/10/2026 · Auteurs : EL BELLAOUI AMR , BENLAAMA Issam

## Contexte
L'API MaintAI reçoit des relevés de capteurs envoyés par d'autres programmes (tableau de bord, application mobile, système de l'atelier). Une valeur impossible, due par exemple à un capteur défaillant ou à une erreur de saisie, ne doit jamais atteindre le modèle, car elle produirait une probabilité de panne sans aucun sens. Il faut donc fixer des bornes pour chaque variable.
Par ailleurs, l'API peut démarrer alors que le fichier `models/model.joblib` est absent (entraînement pas encore lancé, mauvais dossier). Il faut décider de son comportement dans ce cas.

## Options étudiées

### Décision 1 : comment fixer les bornes de chaque variable
1. **Bornes tirées des données** (min et max de `sensors.csv`) : faciles à calculer. Inconvénient : une machine réelle légèrement hors de l'échantillon (un moteur un peu plus chaud que ceux du jeu de données) serait refusée à tort. Les bornes changeraient aussi à chaque nouveau jeu de données.
2. **Bornes physiques** (ce qu'un moteur réel peut afficher) : elles rejettent seulement les valeurs impossibles et acceptent toutes les situations réelles, même rares. Inconvénient : elles demandent de connaître le matériel, et elles sont larges, donc une valeur fausse mais plausible passe quand même.

### Décision 2 : que faire si le modèle est absent
1. **Démarrer quand même et répondre 503 sur `/v1/predict`** : l'API reste joignable, `/health` indique `"model_loaded": false` et `/docs` reste consultable, ce qui facilite le diagnostic. Le message du 503 dit quoi faire. Inconvénient : le service paraît « en vie » alors qu'il ne peut pas prédire. Si personne ne surveille `/health`, la panne peut passer inaperçue.
2. **Refuser de démarrer** (le processus s'arrête avec une erreur) : la panne est visible immédiatement, et il n'existe jamais d'API qui tourne sans pouvoir répondre. Inconvénients : on perd `/health` et `/docs` pour diagnostiquer. Les clients reçoivent une erreur de connexion au lieu d'un message clair, et un orchestrateur risque de redémarrer le service en boucle.

## Décision

**Décision 1 : des bornes physiques**, déclarées dans `SensorReading` (`maintai/api/schemas.py`), toutes en `float` :

| Variable | Min | Max | Justification |
|---|---|---|---|
| `temperature_c` | -40 | 150 | -40 °C couvre un atelier non chauffé en hiver ; au-delà de 150 °C, les isolants d'un moteur industriel sont détruits, la mesure est donc une erreur de capteur. |
| `vibration_mm_s` | 0 | 50 | Une vitesse de vibration ne peut pas être négative ; la norme ISO 10816 place la zone dangereuse vers 7 à 11 mm/s, et 50 mm/s laisse de la marge pour une machine très dégradée. |
| `load_pct` | 0 | 150 | De 0 % (à vide) à la surcharge temporaire ; un moteur ne tient pas au-delà de 150 % de sa charge nominale. |
| `runtime_hours` | 0 | 200 000 | Un compteur d'heures n'est jamais négatif ; 200 000 h font environ 23 ans de marche continue. Type `float` pour accepter 15000,5 h. |

Raison principale : le rôle de la validation est de rejeter l'**impossible**, pas l'**inhabituel**. Une machine en mauvais état est justement celle pour laquelle on veut une prédiction.

**Décision 2 : démarrer et répondre 503.** Raison principale : l'API sert plusieurs clients, qui doivent recevoir une réponse claire et exploitable (« service indisponible, réessayez ») plutôt qu'une erreur de connexion. Le 503 distingue aussi ce cas d'un bug (500), et `/health` permet de détecter le problème.

## Conséquences
- **Ce qui est facilité** : FastAPI renvoie automatiquement un 422 qui indique le champ fautif et la borne dépassée. Le modèle ne voit jamais de valeur impossible. Les bornes sont visibles dans `/docs` pour les développeurs des clients. Un modèle manquant se diagnostique facilement grâce à `/health` et au message du 503.
- **Ce qui devient plus difficile** : une valeur fausse mais plausible (une température de 90 °C mesurée par un capteur déréglé) passe la validation. Changer de type de machine (moteur haute température) obligera à revoir les bornes, et donc la version du contrat (`/v2`).
- **À surveiller** : il faut surveiller `/health` en production, car une API démarrée sans modèle répond 503 à toutes les prédictions sans s'arrêter. Il faut aussi suivre le nombre de 422 : une hausse soudaine signale probablement un capteur défaillant sur le terrain.
