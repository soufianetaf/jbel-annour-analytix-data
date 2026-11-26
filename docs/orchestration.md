# Orchestration (Dagster)

Dagster fait tourner toute la chaîne **toutes les deux heures** (cahier des charges), dans l'ordre que lui donnent les dépendances, et la montre dans une interface web : ce qui a tourné, quand, combien de temps, ce qui a échoué et pourquoi.

## Lancer l'interface

```powershell
$env:DAGSTER_HOME = "$PWD\orchestration\.dagster_home"; uv run dagster dev -m orchestration
```

Puis ouvrir http://localhost:3000. `DAGSTER_HOME` garde l'historique des exécutions (dossier ignoré par Git). Les paramètres de connexion viennent du `.env`, comme pour le reste du projet.

Lancer un chargement complet à la main, sans l'interface :

```powershell
$env:DAGSTER_HOME = "$PWD\orchestration\.dagster_home"; uv run dagster job execute -m orchestration -j chargement_complet
```

## Ce qui tourne, dans l'ordre

| Étape | Actifs Dagster | Ce qui se passe |
|---|---|---|
| 1. Copies | `copie_x3_ventes`, `copie_x3_finance`, `copie_x3_stock`, `copie_x3_achats`, `copie_x3_commandes`, `copie_usine_magasin`, `copie_usine_production`, `copie_usine_machines`, `copie_usine_electricite`, `copie_usine_qualite`, `copie_usine_maintenance`, `copie_usine_rh` | Chaque module `ingestion.*` copie ses tables (86 tables brutes) puis les **rapproche de la source**. Un écart fait échouer la copie |
| 2. dbt | `staging/…`, `intermediate/…`, `marts/…`, `snapshots/…` | `dbt build` : modèles, tests, photos quotidiennes, historique de la qualité des données |
| 3. Contrôles | `rapprochements_metier` | CA, créances, résultat, trésorerie, stock et achats : Sage X3 contre les tables finales |

**Chaque copie est reliée aux modèles qui la lisent** : la clé d'une table brute dans Dagster est son nom exact dans l'entrepôt (`raw_x3/sinvoice`, `raw_rh/effectifs_service`…), et les sources dbt pointent sur ces mêmes tables. Si une copie échoue, Dagster ne reconstruit pas les modèles qui en dépendent : on garde les chiffres d'avant, justes, plutôt que des chiffres faux.

**Une étape à la fois** (exécuteur `in_process`) : les serveurs sources sont en production ; on ne les sollicite jamais en parallèle. Toutes les lectures restent en lecture seule, sans verrou, comme à la main.

## Planification et alerte

| Élément | Réglage |
|---|---|
| `toutes_les_deux_heures` | `0 */2 * * *`, fuseau `Africa/Casablanca`. **Créée arrêtée** : on l'active dans l'interface (Automation → toutes_les_deux_heures → Start) quand on le décide |
| Jamais deux chargements à la fois | Si le chargement précédent tourne encore, le suivant est sauté (« SkipReason ») |
| `alerte_echec` | Active dès le démarrage : un chargement en échec est écrit en erreur dans le journal de Dagster, avec la raison |

## Tests (`tests/test_orchestration.py`, job « Projet dbt » de la CI)

| Test | Ce qu'il vérifie |
|---|---|
| Chaque module de copie est orchestré | Un nouveau module `ingestion.*` oublié dans `MODULES_COPIE` fait échouer le test |
| Chaque source dbt brute a sa copie | Une source `raw_…` lue par dbt mais produite par aucune copie ne serait jamais rechargée |
| Les rapprochements suivent dbt | Ils dépendent des 6 tables finales qu'ils contrôlent |
| Un seul job, séquentiel | Exécuteur `in_process` |
| Planification | Toutes les deux heures, fuseau de Casablanca, créée arrêtée ; lance un chargement si rien ne tourne, **saute** si le précédent tourne encore |
| Alerte | Le capteur d'échec est actif |

## Essai réel (26/11/2026)

Copie de la qualité puis modèles dbt qui en dépendent, lancés par Dagster : 6 tables copiées et rapprochées, 41 modèles et tests dbt (0 erreur), exécution en succès.

## Points à valider

1. **Où tournera Dagster en production** (serveur, service Windows ou Linux) ? En production, les variables viennent de l'environnement du service, pas d'un fichier `.env`.
2. **Alerte par courriel** : quel serveur de messagerie, et qui prévenir ?
3. Fréquence : toutes les deux heures, toute la journée ? Ou seulement de 6 h à 22 h ?
4. Quand activer la planification sur les serveurs de production (après accord des responsables des sources).
