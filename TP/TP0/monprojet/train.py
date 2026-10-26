"""Entraîne chaque modèle candidat, l'évalue sur le jeu de test et les compare.

Usage, depuis la racine du projet : python -m monprojet.train
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score)
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from monprojet import config
from monprojet.data import load_data, split
from monprojet.models import candidates

HIGHER_IS_BETTER = {"accuracy": True, "recall": True, "precision": True, "f1": True,
                    "mae": False, "rmse": False, "r2": True}


def build_preprocessing(X: pd.DataFrame) -> ColumnTransformer:
    """Prépare les colonnes : nombres mis à l'échelle, catégories encodées, texte vectorisé. (Fournie.)"""
    text = [config.TEXT_COLUMN] if config.TEXT_COLUMN else []
    numeric = [c for c in X.columns if c not in text and pd.api.types.is_numeric_dtype(X[c])]
    categorical = [c for c in X.columns if c not in text and c not in numeric]
    steps = []
    if numeric:
        steps.append(("nombres", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric))
    if categorical:
        steps.append(("categories", make_pipeline(SimpleImputer(strategy="most_frequent"),
                                                  OneHotEncoder(handle_unknown="ignore")), categorical))
    if text:
        steps.append(("texte", TfidfVectorizer(), config.TEXT_COLUMN))
    return ColumnTransformer(steps, sparse_threshold=0)


def evaluate(model, X_test, y_test) -> dict:
    """Prédit sur le jeu de test et renvoie {nom de la métrique: valeur}, arrondie à 3 décimales."""
    y_pred = model.predict(X_test)

    if config.TASK == "classification":
        average = "binary" if len(np.unique(y_test)) == 2 else "macro"
        scores = {
            "accuracy": accuracy_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred, average=average, zero_division=0),
            "precision": precision_score(y_test, y_pred, average=average, zero_division=0),
            "f1": f1_score(y_test, y_pred, average=average, zero_division=0),
        }
    else:
        scores = {
            "mae": mean_absolute_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "r2": r2_score(y_test, y_pred),
        }
    return {nom: round(float(valeur), 3) for nom, valeur in scores.items()}


def main() -> None:
    """Entraîne chaque candidat, l'évalue, compare, et sauvegarde le meilleur."""
    # 1. Charger et découper
    df = load_data()
    X_train, X_test, y_train, y_test = split(df)

    # 2. Entraîner sur X_train, évaluer sur X_test (le test ne sert qu'à mesurer)
    resultats, modeles = {}, {}
    for nom, estimateur in candidates().items():
        model = Pipeline([
            ("preparation", build_preprocessing(X_train)),
            ("modele", estimateur),
        ])
        model.fit(X_train, y_train)
        resultats[nom] = evaluate(model, X_test, y_test)
        modeles[nom] = model

    # 3. Tableau de comparaison, trié selon la métrique principale
    metrique = config.MAIN_METRIC
    plus_grand_mieux = HIGHER_IS_BETTER[metrique]
    tableau = pd.DataFrame(resultats).T.sort_values(metrique, ascending=not plus_grand_mieux)
    print(f"\nComparaison sur le jeu de test (métrique principale : {metrique})\n")
    print(tableau.to_string())

    # 4. Meilleur modèle (idxmin pour mae / rmse)
    meilleur = tableau[metrique].idxmax() if plus_grand_mieux else tableau[metrique].idxmin()
    print(f"\nMeilleur modèle : {meilleur} ({metrique} = {resultats[meilleur][metrique]})")

    # 4 bis. Baseline métier : la prévision utilisée aujourd'hui, sur le même jeu de test
    baseline_metier = None
    colonne = getattr(config, "NAIVE_COLUMN", None)
    if config.TASK == "regression" and colonne:
        manquants = int(X_test[colonne].isna().sum())
        # Après des vacances, pas de « semaine précédente » : on prend la moyenne de l'entraînement
        prevision = X_test[colonne].fillna(y_train.mean())
        baseline_metier = {
            "mae": round(float(mean_absolute_error(y_test, prevision)), 3),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, prevision))), 3),
            "r2": round(float(r2_score(y_test, prevision)), 3),
        }
        ecart = 1 - resultats[meilleur]["mae"] / baseline_metier["mae"]
        print(f"\nBaseline métier ({colonne}) : {baseline_metier} "
              f"({manquants} jour(s) sans valeur, remplacés par la moyenne)")
        print(f"MAE du meilleur modèle : {ecart:.1%} sous la baseline métier")

    # 5. Sauvegarde du modèle et des métriques
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(modeles[meilleur], config.MODELS_DIR / "model.joblib")
    contenu = {"main_metric": metrique, "best": meilleur, "results": resultats,
               "baseline_metier": baseline_metier}
    (config.MODELS_DIR / "metrics.json").write_text(
        json.dumps(contenu, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()