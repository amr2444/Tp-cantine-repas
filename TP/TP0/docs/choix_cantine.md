\# Choix du modèle — CantineAI (prévision du nombre de repas)



\## Contexte et métrique



\- \*\*Problème\*\* : régression sur une série temporelle, prévoir `repas\_servis` pour le

&#x20; lendemain, chaque jour d'école à 10 h.

\- \*\*Données\*\* : `data/cantine\_repas.csv`, 340 jours d'école (sept. 2024 → juin 2026),

&#x20; données synthétiques générées pour le cours.

\- \*\*Découpage chronologique\*\* : entraînement sur les 272 jours les plus anciens, test sur

&#x20; les 68 jours les plus récents (20 %). Le modèle apprend le passé et il est testé sur le

&#x20; futur, comme en usage réel. Un découpage aléatoire lui ferait « voir l'avenir ».

\- \*\*Métrique principale : MAE en repas.\*\* Elle se lit directement (« on se trompe en moyenne

&#x20; de N repas par jour ») et chaque repas d'écart a un coût : \~15 DH et du gaspillage s'il

&#x20; est en trop, un élève sans déjeuner ou un sandwich d'urgence s'il manque.

\- \*\*Baseline métier\*\* : la méthode actuelle du gestionnaire, qui reprend le nombre de repas

&#x20; du même jour la semaine précédente (`repas\_semaine\_precedente`). Après des vacances,

&#x20; cette valeur n'existe pas (10 jours du test) : on la remplace par la moyenne de

&#x20; l'entraînement.

\- \*\*Critère d'acceptation\*\* : MAE au moins 15 % sous la baseline métier, sur les 68 jours

&#x20; de test.



\## Résultats sur le jeu de test (68 jours)



| Modèle                               | MAE (repas) | RMSE | R²     |

|--------------------------------------|------------:|-----:|-------:|

| \*\*Régression linéaire\*\*              | \*\*22,2\*\*    | 28,2 | 0,883  |

| Forêt aléatoire                      | 31,8        | 41,6 | 0,745  |

| Gradient boosting                    | 39,0        | 51,0 | 0,616  |

| Baseline : toujours la moyenne       | 70,3        | 88,4 | −0,151 |

| Baseline métier : semaine précédente | 76,0        | 95,6 | −0,346 |



\## Modèle retenu : régression linéaire



\*\*Critère d'acceptation : atteint.\*\* MAE de 22,2 contre 76,0 pour la baseline métier, soit

\*\*70,7 % d'erreur en moins\*\* (critère : au moins 15 %).



\*\*Pourquoi la régression linéaire ?\*\*

\- C'est la meilleure sur la métrique choisie, avec une MAE 30 % plus faible que la forêt

&#x20; aléatoire.

\- Avec 272 jours d'entraînement, les modèles à arbres ont trop peu d'exemples. Les effets

&#x20; semblent surtout additifs (une sortie scolaire ou des examens retirent un nombre de repas

&#x20; à peu près fixe), ce que capte bien un modèle linéaire.

\- Elle est simple, rapide et interprétable : ses coefficients montrent l'effet de chaque

&#x20; facteur (menu, météo, examens…), ce qui est utile pour l'expliquer au gestionnaire.



\*\*Constat sur la méthode actuelle\*\* : elle fait moins bien que la simple moyenne

(MAE 76,0 contre 70,3). En recopiant la semaine précédente, elle reporte des événements

ponctuels (examens, sorties, veille de vacances) sur une semaine où ils n'ont plus lieu.

Le modèle, lui, utilise ce qu'on sait la veille : menu, météo prévue, calendrier.



\## Limites



\- \*\*La MAE traite pareil un repas en trop et un repas manquant\*\*, alors qu'un élève sans

&#x20; déjeuner est plus grave que 15 DH perdus. Il faudrait analyser le signe des erreurs, et

&#x20; éventuellement ajouter une petite marge de sécurité à la prévision.

\- \*\*Peu de données\*\* : 340 jours, dont 68 de test. Le score dépend de la période testée

&#x20; (fin d'année scolaire, avec examens). Une validation sur plusieurs périodes successives

&#x20; serait plus solide.

\- \*\*Données synthétiques\*\* : les vraies données d'une cantine seront plus bruitées

&#x20; (absences, grèves, épidémies…). Les performances réelles seront sûrement moins bonnes.

\- \*\*10 jours de test sans « semaine précédente »\*\* (retours de vacances) : notre choix de

&#x20; les remplacer par la moyenne influence légèrement le score de la baseline métier.

\- \*\*Pas de réglage des hyperparamètres\*\* ni de réentraînement au fil de l'année. En

&#x20; production, il faudrait réentraîner régulièrement avec les nouveaux jours.

