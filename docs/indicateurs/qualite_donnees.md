# Fiche indicateur : qualité des données

> **Statut : en service. Les services responsables sont à confirmer avec chaque responsable.**

| Élément | Valeur |
|---|---|
| Domaine | Qualité des données (tous les services) |
| Responsable | Responsable du projet Analytix ; chaque service corrige ses propres sources |
| Tables | `marts.agg_qualite_donnees` (un contrôle, vue), `qualite_donnees.resultats_tests` (historique), `qualite_donnees.<test>` (lignes en erreur d'un contrôle) |
| Mise à jour | À chaque `dbt build` ou `dbt test`, automatiquement |

## Le principe

Les contrôles dbt en **avertissement** trouvent des erreurs dans les sources : un poids d'article faux dans Sage X3, une quantité impossible dans une application de l'usine… Ils ne bloquent pas la chaîne : la valeur impossible est déjà écartée des calculs, mais elle doit être corrigée **à la source, par le service qui l'a saisie**. Analytix n'écrit jamais dans les sources.

Cette page dit à chaque service **quoi corriger, où, et combien de lignes il reste**. Quand une ligne est corrigée dans la source, elle disparaît au contrôle suivant, et l'évolution le montre.

## Comment ça marche

1. Chaque avertissement porte dans sa configuration dbt :
   - `store_failures: true` : ses lignes en erreur sont gardées dans le schéma `qualite_donnees`, une table par contrôle, remplacée à chaque contrôle ;
   - `meta.service` : le service qui corrige ;
   - `meta.correction` : ce qu'il faut corriger, et où.
   Un test pytest (`tests/test_qualite_donnees.py`) refuse tout nouvel avertissement sans ces trois informations.
2. À la fin de chaque construction, la macro `enregistrer_resultats_tests` (hook `on-run-end`) ajoute à `qualite_donnees.resultats_tests` le résultat de chaque contrôle suivi : date, statut, nombre de lignes en erreur, service, correction, table des lignes. Les contrôles qui passent sont enregistrés aussi : c'est ce qui montre une correction.
3. La vue `marts.agg_qualite_donnees` donne, par contrôle, le dernier résultat et l'évolution :

```
lignes_en_erreur          = lignes en erreur au dernier contrôle
lignes_controle_precedent = au contrôle d'avant
evolution                 = lignes_en_erreur - lignes_controle_precedent (négatif : des lignes corrigées)
premiere_erreur_le        = premier contrôle où le test a trouvé des erreurs
```

C'est une **vue** : l'historique est écrit à la fin de la construction, après les modèles, et une table aurait toujours un contrôle de retard.

## Accès

- La vue `agg_qualite_donnees` est dans `marts` : l'API pourra la montrer (nombre de lignes par service).
- Les **tables des lignes en erreur** (`qualite_donnees.*`) contiennent des données métier (montants de DA, factures…) : elles ne sont pas ouvertes à l'API pour l'instant. L'étape API dira quel rôle voit le détail de quel service.
- Aucune donnée RH n'y est gardée : le contrôle RH (`assert_rh_aucun_petit_groupe_nomme`) est bloquant et ne garde pas ses lignes.

## État au 26/11/2026 : 329 lignes à corriger

| Service | Contrôles | Lignes |
|---|---|---|
| Achats | montant des demandes d'achat (85) | 85 |
| ADV | représentant des lignes de facture (63), nom des clients (9) | 72 |
| Production | rapports de consommations (31), lignes sans fiche de poste (20) | 51 |
| Gestion des articles | poids des briques dans Sage X3 | 31 |
| Automatisme | cycles de wagons (20), compteurs remis à zéro (4) | 24 |
| Comptabilité fournisseurs | en-tête ≠ lignes des factures | 22 |
| Qualité | quantités non acceptables | 20 |
| Magasin | quantités (9) et kilométrages (2) de gasoil | 11 |
| Comptabilité | écritures datées de 2027 (8), pièce sur le mauvais exercice (1) | 9 |
| Contrôle de gestion | coût moyen (CMUP) aberrant | 4 |
| Comptabilité clients | (devise, tiers sans fiche : aucune erreur) | 0 |

## Points à valider

1. Le service responsable de chaque contrôle, avec les responsables concernés.
2. Qui voit le détail des lignes en erreur (le service seul, ou aussi la direction) ?
3. Faut-il prévenir chaque service quand ses erreurs augmentent (courriel), une fois l'orchestration en place ?
