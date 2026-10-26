# Compte rendu · TP1 : une API de prédiction pour MaintAI

  **Membres :** [EL BELLOAUI Amr , BENLAAMA Issam]  ·  **Date :** 26/10/2026

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed, 1 warning
```

Les 4 tests de `tests/test_api.py` qui passent déjà : [À COMPLÉTER : les noms des 4 tests qui ne sont pas FAILED dans test_api.py]

Les deux tests qui attendent un code 422 passent « pour une mauvaise raison ». Au départ, `SensorReading` ne déclare aucun champ, et sa configuration contient `extra="forbid"`, qui refuse tout champ inconnu. Les quatre champs envoyés (`temperature_c`, etc.) sont donc tous « inconnus », et **n'importe quel relevé est refusé avec 422**, même un relevé parfaitement valide. Ces tests obtiennent le bon code sans vérifier ce qu'ils prétendent vérifier, c'est-à-dire qu'une valeur hors bornes est rejetée. Un test vert ne prouve rien tant qu'on ne sait pas pourquoi il passe.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | float | -40 | 150 | -40 °C couvre un atelier non chauffé en hiver ; au-delà de 150 °C, les isolants d'un moteur industriel (classe H : 180 °C au point chaud) sont détruits, une telle mesure est donc une erreur de capteur. |
| `vibration_mm_s` | float | 0 | 50 | Une vitesse de vibration efficace ne peut pas être négative. La norme ISO 10816 classe une machine en zone dangereuse vers 7 à 11 mm/s ; 50 mm/s laisse de la marge pour une machine très dégradée sans accepter une valeur absurde. |
| `load_pct` | float | 0 | 150 | La charge va de 0 % (à vide) à plus de 100 % en surcharge temporaire ; un moteur ne tient pas durablement au-delà de 150 % de sa charge nominale. |
| `runtime_hours` | float | 0 | 200000 | Un compteur d'heures ne peut pas être négatif ; 200 000 h, c'est environ 23 ans de marche continue, plus que la durée de vie d'un moteur. Type `float` et pas `int` : 15000,5 h doit être accepté. |

Les bornes ne sont pas copiées sur le min et le max de `sensors.csv`. Sinon, une machine réelle un peu plus chaude que celles du jeu de données serait refusée à tort.

Après avoir écrit `schemas.py` seul :

```
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed, 1 warning in 5.52s
```

C'est un bon signe : l'erreur n'est plus un 422. Les relevés valides passent maintenant la validation et la requête arrive jusqu'à `predict()`, qui n'est pas encore écrite (`NotImplementedError`). Les deux tests 422 passent désormais pour la bonne raison : seules les valeurs hors bornes sont refusées.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez uvicorn.",
        )
    result = predictor.predict(reading.model_dump())
    return PredictionOut(**result)
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Un 500 signifie « bug dans le code du serveur ». Or le code est correct : c'est le service qui n'est pas prêt, car le fichier `models/model.joblib` est absent. Le 503 (« service indisponible ») dit précisément cela au client : il peut réessayer plus tard, et ce n'est pas sa requête qui est en cause. Le message `detail` indique en plus quoi faire pour réparer. Sans la vérification, `None.predict(...)` lèverait une exception et FastAPI renverrait un 500 trompeur.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Charger le modèle depuis le disque (`joblib.load`) est lent par rapport à une prédiction. Le recharger à chaque requête multiplierait le temps de réponse et la charge disque pour rien, puisque le modèle ne change pas entre deux requêtes. Il est donc chargé une fois dans `lifespan`, gardé en mémoire dans le dictionnaire `state`, puis réutilisé par toutes les requêtes. Autre avantage : on sait dès le démarrage si le modèle manque, et `/health` le signale.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning in 15.51s
```

## 5. L'API en marche

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status": "ok", "model_loaded": true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | [À COMPLÉTER : copier le JSON affiché, de la forme `{"failure_probability": ..., "alert": ..., "threshold": 0.3, "model_version": "..."}`] |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail": [{"type": "less_than_equal", "loc": ["body", "temperature_c"], "msg": "Input should be less than or equal to 150", "input": 500, "ctx": {"le": 150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail": "Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la section **Schemas** en bas de la page, en dépliant `SensorReading`, et dans l'onglet **Schema** du corps de requête de `POST /v1/predict`. Chaque champ y affiche son type (`number`), son `minimum`, son `maximum` et sa description.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un ensemble de règles pour concevoir une API web : des URL claires, les méthodes HTTP (GET, POST), des codes de statut précis, du JSON en entrée et en sortie, une version dans l'adresse. FastAPI est une bibliothèque Python qui permet d'écrire une API respectant ces règles. REST est la norme, FastAPI est l'outil, et uvicorn est le programme qui fait tourner l'API.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   (1) **Valider** chaque requête avant d'appeler la fonction : une valeur hors bornes renvoie 422 et n'atteint jamais le modèle. (2) **Documenter** : FastAPI génère automatiquement la page `/docs` avec les champs, leurs types, leurs bornes et un exemple. (3) **Donner un objet Python typé** : `reading.temperature_c` est un `float` déjà vérifié, et `reading.model_dump()` le transforme en dictionnaire pour le modèle. Les trois viennent du même endroit et ne peuvent donc pas se contredire.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` désigne la machine elle-même : le serveur tourne sur mon PC. `8000` est le port, la « porte » sur laquelle uvicorn écoute. `/v1/predict` est la route, un chemin défini dans le code Python (et non un dossier sur le disque), dont `/v1` est la version de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   Pour versionner le contrat de l'API. Si on change un jour les entrées ou les sorties (nouveau capteur, nouveau format de réponse), on peut publier `/v2` tout en gardant `/v1` en service. Les clients existants (tableau de bord, application mobile, système de l'atelier) ne sont pas cassés et migrent à leur rythme.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le module Python, c'est-à-dire le fichier `maintai/api/main.py` écrit avec des points et sans `.py`. `app` est la variable de ce fichier qui contient l'application (`app = FastAPI(...)`), celle que uvicorn doit faire tourner.


## 8. Ce qui reste flou

Ce que je n'ai pas compris c'est comment l'API sera protégée par une clé dans la prochaine séance 5