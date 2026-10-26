"""Les modèles à comparer.

candidates() renvoie la baseline puis plusieurs vrais modèles, adaptés à config.TASK.
"""
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.linear_model import LinearRegression, LogisticRegression

from monprojet import config


def candidates() -> dict:
    """Renvoie un dictionnaire {nom: modèle scikit-learn non entraîné}.

    - le premier modèle est la baseline (DummyClassifier / DummyRegressor) ;
    - puis au moins trois vrais modèles, adaptés à config.TASK ;
    - random_state=config.SEED pour les modèles qui ont du hasard.
    """
    if config.TASK == "classification":
        return {
            "baseline": DummyClassifier(strategy="most_frequent"),
            "regression_logistique": LogisticRegression(max_iter=1000),
            "regression_logistique_equilibree": LogisticRegression(max_iter=1000,
                                                                   class_weight="balanced"),
            "foret_aleatoire": RandomForestClassifier(n_estimators=200, random_state=config.SEED),
            "gradient_boosting": HistGradientBoostingClassifier(random_state=config.SEED),
        }
    return {
        "baseline": DummyRegressor(strategy="mean"),
        "regression_lineaire": LinearRegression(),
        "foret_aleatoire": RandomForestRegressor(n_estimators=200, random_state=config.SEED),
        "gradient_boosting": HistGradientBoostingRegressor(random_state=config.SEED),
    }