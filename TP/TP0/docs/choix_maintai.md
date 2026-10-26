\# Choix du modèle — MaintAI (prédiction de pannes)



\## Contexte et métrique



\- \*\*Problème\*\* : classification binaire, prédire si un relevé de capteurs se termine par une panne (1) ou non (0).

\- \*\*Données\*\* : `data/exemple\_pannes.csv`, 5 000 relevés, 17,6 % de pannes.

\- \*\*Découpage\*\* : aléatoire, stratifié, 20 % en test (1 000 relevés, tenus à l'écart), graine 42.

&#x20; Tous les modèles sont évalués sur ce même jeu de test.

\- \*\*Métrique principale : le rappel.\*\* Une panne manquée arrête une ligne de production

&#x20; une journée, alors qu'une fausse alerte coûte une heure d'inspection. Rater une panne

&#x20; coûte donc bien plus cher qu'une fausse alerte : on cherche d'abord à détecter le plus

&#x20; de pannes possible.

\- \*\*Critère d'acceptation\*\* : rappel ≥ 0,75 \*\*et\*\* précision ≥ 0,50 sur le jeu de test.

&#x20; La contrainte sur la précision évite de noyer l'équipe sous les fausses alertes.



\## Résultats sur le jeu de test



| Modèle                               | Accuracy | Rappel    | Précision | F1    |

|--------------------------------------|---------:|----------:|----------:|------:|

| \*\*Régression logistique équilibrée\*\* | 0,839    | \*\*0,847\*\* | 0,527     | 0,649 |

| Gradient boosting                    | 0,881    | 0,574     | 0,697     | 0,629 |

| Régression logistique                | 0,889    | 0,574     | 0,737     | 0,645 |

| Forêt aléatoire                      | 0,881    | 0,557     | 0,705     | 0,622 |

| Baseline (toujours « pas de panne ») | 0,824    | 0,000     | 0,000     | 0,000 |



\## Modèle retenu : régression logistique avec `class\_weight="balanced"`



\*\*Écart avec la baseline\*\* : le rappel passe de 0 à 0,847. La baseline ne détecte aucune

panne malgré 82,4 % d'accuracy, ce qui montre que l'accuracy est trompeuse quand une

classe est rare.



\*\*Critère d'acceptation : atteint.\*\* Rappel 0,847 ≥ 0,75 et précision 0,527 ≥ 0,50.



\*\*Pourquoi ce modèle plutôt que celui à la meilleure accuracy ?\*\*

La régression logistique simple a la meilleure accuracy (0,889) mais un rappel de

seulement 0,574 : elle échoue au critère. Sur les \~176 pannes du jeu de test :



|                  | Logistique équilibrée | Logistique simple |

|------------------|-----------------------|-------------------|

| Pannes détectées | \~149                  | \~101              |

| Pannes manquées  | \~27                   | \~75               |

| Fausses alertes  | \~134                  | \~36               |



Le modèle équilibré détecte environ 48 pannes de plus, au prix d'environ 98 fausses

alertes de plus. Cela représente \~48 journées d'arrêt évitées contre \~98 heures

d'inspection supplémentaires : un échange très favorable vu les coûts de MaintAI.



`class\_weight="balanced"` donne plus de poids aux pannes (classe minoritaire) pendant

l'entraînement. Le modèle prédit donc « panne » plus souvent, ce qui augmente le rappel

et baisse la précision.



C'est aussi un modèle simple, rapide et interprétable : les coefficients indiquent

quelles variables (température, vibration…) poussent vers une panne.



\## Limites



\- \*\*Précision tout juste au-dessus du seuil (0,527)\*\* : environ une alerte sur deux est

&#x20; fausse. La marge est faible, un autre découpage pourrait passer sous 0,50.

\- \*\*Un seul découpage\*\* : les scores dépendent des 1 000 relevés tirés pour le test.

&#x20; Une validation croisée sur l'entraînement donnerait une estimation plus stable.

\- \*\*Seuil de décision par défaut (0,5)\*\* : on n'a pas réglé le seuil de probabilité,

&#x20; qui permettrait d'ajuster finement le compromis rappel / précision. Il faudrait le

&#x20; régler sur un jeu de validation, pas sur le test.

\- \*\*Pas de réglage des hyperparamètres\*\* des forêts et du gradient boosting. Leurs

&#x20; versions avec `class\_weight="balanced"` n'ont pas été essayées : elles pourraient

&#x20; faire mieux.

\- \*\*Pas de dimension temporelle\*\* : le découpage est aléatoire. En production, le modèle

&#x20; prédira le futur ; un découpage chronologique serait plus réaliste si les relevés

&#x20; sont datés.

\- \*\*Données limitées\*\* : 5 000 relevés, quatre variables, une seule usine. Rien ne

&#x20; garantit que le modèle se généralise à d'autres machines.

