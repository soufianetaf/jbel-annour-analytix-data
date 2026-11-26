# Jbel Annour Analytix

Plateforme d’analyse des données de Jbel Annour : chaque service voit ses chiffres, à jour, dans un seul outil, avec les mêmes définitions pour tout le monde.

Ce document s’adresse à **quelqu’un qui arrive sur le projet et ne connaît rien** : ni l’entreprise, ni ses données, ni les outils. Lisez-le dans l’ordre : chaque partie s’appuie sur la précédente.

> **Statut :** projet au démarrage. Ce document décrit ce que l’on va construire et comment. Le code arrive étape par étape.

> **Périmètre de ce dépôt :** le **data warehouse** (ingestion, dbt, orchestration) et l’**API** (FastAPI). L’interface web (React) est développée dans un **dépôt séparé**, qui ne fait qu’appeler cette API.

---

## Sommaire

1. [En une minute](#1-en-une-minute)
2. [L’entreprise et le problème](#2-lentreprise-et-le-problème)
3. [Ce que fera Analytix](#3-ce-que-fera-analytix)
4. [Les mots à connaître](#4-les-mots-à-connaître)
5. [D’où viennent les données](#5-doù-viennent-les-données)
6. [Le trajet des données](#6-le-trajet-des-données)
7. [Le modèle en étoile, expliqué simplement](#7-le-modèle-en-étoile-expliqué-simplement)
8. [Quand les données changent](#8-quand-les-données-changent)
9. [Les outils utilisés et pourquoi](#9-les-outils-utilisés-et-pourquoi)
10. [Organisation du dépôt](#10-organisation-du-dépôt)
11. [Comment on travaille](#11-comment-on-travaille)
12. [Les règles d’or](#12-les-règles-dor)
13. [Préparer son poste](#13-préparer-son-poste)
14. [Les pièges connus dans les données](#14-les-pièges-connus-dans-les-données)
15. [Feuille de route](#15-feuille-de-route)
16. [Questions encore ouvertes](#16-questions-encore-ouvertes)
17. [Pour aller plus loin](#17-pour-aller-plus-loin)

---

## 1. En une minute

- **Jbel Annour** fabrique et vend des briques. L’entreprise fait partie d’un groupe de plusieurs sociétés.
- Ses données sont éparpillées dans **45 bases de données** : le logiciel de gestion **Sage X3**, et une quarantaine d’applications internes (machines, production, maintenance, magasin, pointage…).
- **Analytix** copie ces données, **sans jamais les modifier**, dans un entrepôt unique (un *data warehouse*), les nettoie, les vérifie, puis les affiche :
  - dans une **plateforme web** où chacun ne voit que ce que son rôle autorise (l’API est dans ce dépôt, l’interface dans un dépôt séparé) ;
  - dans **Power BI**, pour les analyses libres, avec exactement les mêmes chiffres.
- On construit **un service à la fois**, de bout en bout, en commençant par la finance.

---

## 2. L’entreprise et le problème

### L’usine en quelques mots

Pour comprendre les données, il faut comprendre la fabrication d’une brique :

```
Argile + combustibles  →  Préparation  →  Moulage  →  Séchoir  →  Empileuse  →  Four  →  Dépileuse  →  Stock  →  Vente
   (dosage)                               (extrudeuse)  (étagères)   (wagons)                (paquets)
```

- **Préparation** : on dose l’argile avec du charbon, du coke ou de la biomasse.
- **Moulage** : une extrudeuse pousse l’argile et la coupe en briques.
- **Séchoir** : les briques sèchent sur des étagères.
- **Empileuse** : les briques sèches sont chargées sur des wagons.
- **Four** : les wagons traversent le four, chauffé au coke et au fuel.
- **Dépileuse** : les briques cuites sont déchargées et emballées en paquets.
- Puis viennent le **stock**, la **vente**, la **livraison** et la **facturation**.

Autour de la production, d’autres services font tourner l’entreprise : maintenance, magasin et achats, qualité, commercial, finance, ressources humaines.

### Le problème à résoudre

- Chaque service regarde ses propres outils. **Personne n’a de vue d’ensemble.**
- Les chiffres d’un service ne se croisent pas avec ceux d’un autre. Exemple : on ne sait pas facilement combien d’électricité et de coke il a fallu pour produire une tonne de briques.
- Des indicateurs essentiels ne sont **calculés nulle part** : le coût de revient réel par tonne, la marge réelle par type de brique.
- Certaines données contiennent des erreurs que personne ne voit (voir la [partie 14](#14-les-pièges-connus-dans-les-données)).

---

## 3. Ce que fera Analytix

### Les objectifs

1. **Centraliser** les données de tous les services dans un seul entrepôt, mis à jour automatiquement.
2. **Donner à chacun les analyses de son rôle**, et seulement celles-là.
3. **Croiser les services** pour obtenir ce qu’aucun outil ne donne seul (coût par tonne, marge, impact des pannes).
4. **Alimenter Power BI** avec les mêmes tables, pour que les chiffres soient identiques partout.
5. **Rendre visibles les erreurs dans les données**, et dire à quel service les corriger.

### Qui verra quoi

| Rôle | Ce qu’il voit |
|---|---|
| Direction générale | Tous les services, toutes les sociétés du groupe |
| Directeur commercial | Ventes, livraisons, clients, créances clients |
| Représentant | Uniquement ses clients et ses ventes |
| Responsable production | Production, machines, énergie, qualité |
| Responsable maintenance | Pannes, interventions, pièces de rechange |
| Acheteur / magasinier | Achats, magasin, stock, fournisseurs |
| Finance / contrôle de gestion | Comptabilité, trésorerie, budget, coûts, marges |
| RH | Effectifs, pointage, absentéisme (jamais les salaires individuels) |
| Administrateur | Comptes et droits, pas les données métier |

### Exemples d’indicateurs

- **Commercial :** chiffre d’affaires, évolution sur un an, clients gagnés et perdus, délai entre commande, livraison et facture.
- **Production :** production par poste comparée à l’objectif, temps d’arrêt des machines.
- **Énergie :** kWh et coke par tonne de briques.
- **Maintenance :** nombre de pannes, temps moyen de réparation, pièces consommées.
- **Achats :** délai entre la demande d’achat et la réception, prix par fournisseur.
- **Finance :** créances en retard, trésorerie, compte de résultat, budget comparé au réel.

---

## 4. Les mots à connaître

| Mot | Ce que ça veut dire |
|---|---|
| **Source** | Une base de données qui existe déjà et que l’on lit (Sage X3, une application de l’usine). |
| **Data warehouse** (entrepôt de données) | La base où l’on rassemble des copies des données de toutes les sources, organisées pour l’analyse. Ici : PostgreSQL. |
| **ELT** | *Extract, Load, Transform* : on copie d’abord les données brutes (Extract, Load), puis on les transforme dans l’entrepôt (Transform). |
| **Pipeline** | La chaîne automatique qui copie, transforme et vérifie les données. |
| **Orchestrateur** | Le programme qui lance le pipeline à la bonne heure, dans le bon ordre, et prévient en cas d’erreur. Ici : Dagster. |
| **Couche** | Une étape du trajet des données dans l’entrepôt : brute, nettoyée, enrichie, prête à l’emploi. |
| **Table de faits** | Une table d’événements que l’on compte ou additionne : une vente, une intervention, une mesure. |
| **Dimension** | Une table qui décrit : le client, l’article, la machine, la date. |
| **Grain** | Ce que représente une ligne d’une table. Exemple : « une ligne de facture ». |
| **Incrémental** | Ne copier que ce qui est nouveau ou modifié depuis la dernière fois. |
| **Snapshot** (photo) | Une copie de l’état d’une donnée à un instant donné, pour garder l’historique. |
| **Sécurité par ligne** | Chaque utilisateur ne reçoit que les lignes qu’il a le droit de voir. |
| **dbt** | L’outil qui transforme les données avec du SQL et les teste automatiquement. |
| **Lecture seule** | On a le droit de lire une base, jamais de la modifier. |

**Quelques termes métier :**

| Terme | Sens |
|---|---|
| **Avoir** | Facture négative : un remboursement ou une correction en faveur du client. |
| **CA net** | Chiffre d’affaires des factures, moins les avoirs. |
| **DA** | Demande d’achat, faite par un service avant une commande au fournisseur. |
| **BC** | Bon de commande envoyé au fournisseur. |
| **Échéance** | Date à laquelle une facture doit être payée. |
| **Balance âgée** | Les factures non payées, classées selon leur retard. |
| **OT** | Ordre de travail de maintenance. |
| **MTTR / MTBF** | Temps moyen de réparation / temps moyen entre deux pannes. |
| **cos φ** | Indicateur de qualité de la consommation électrique ; trop bas, il coûte des pénalités. |

---

## 5. D’où viennent les données

Trois grandes familles de sources, toutes sur des serveurs SQL Server de l’entreprise :

| Source | Ce qu’on y trouve | Volume |
|---|---|---|
| **Sage X3, dossier BASE1** | Le logiciel de gestion de Jbel Annour : ventes, achats, stock, comptabilité, trésorerie, immobilisations, ordres de travail de maintenance | Environ 230 millions de lignes, dont beaucoup de journaux techniques inutiles pour nous |
| **Sage X3, dossier du groupe** | Sept sociétés du groupe, pointage, primes, paie | Environ 50 millions de lignes. **Données RH très sensibles** |
| **Applications de l’usine** | Une quarantaine de bases : machines (moulage, four, séchoir, empileuse, dépileuse, électricité), production, qualité, maintenance, magasin, achats, pointage, RH, annuaire des utilisateurs | Environ 2 millions de lignes, dont 1,3 million de mesures du moulage |

**Ce qu’il faut savoir sur ces sources :**

- **Sage X3** a des tables aux noms codés : `SINVOICE` (factures), `SORDER` (commandes), `PORDER` (commandes fournisseurs), `STOJOU` (mouvements de stock), `GACCENTRY` (écritures comptables), `GACCDUDATE` (échéances). Les colonnes finissent par `_0`. Les tables commençant par `X`, `Y` ou `Z` ont été créées spécialement pour Jbel Annour.
- **Les applications de l’usine** ont été développées en interne. Plusieurs existent en double (une ancienne et une récente) : il faut toujours savoir laquelle fait foi.
- **Les machines** envoient des mesures toutes les minutes ou tous les quarts d’heure, mais seulement **depuis fin 2025**.
- **Certaines tables contiennent des données personnelles** (CIN, RIB, salaires, mots de passe). Elles ne sont **jamais** copiées.

Les adresses des serveurs, les comptes et le détail des tables sont dans le cahier des charges confidentiel (voir la [partie 17](#17-pour-aller-plus-loin)), **jamais dans ce dépôt**.

---

## 6. Le trajet des données

```
 SOURCES (lecture seule)
 Sage X3 · dossier groupe · applications de l’usine
        │
        │  1. INGESTION : copie automatique (Python)
        ▼
 ┌──────────────────── DATA WAREHOUSE (PostgreSQL) ─────────────────────┐
 │                                                                       │
 │  raw           copie fidèle de chaque source, jamais modifiée        │
 │   │                                                                   │
 │  staging       nettoyage : noms clairs, bons types, vides corrigés   │
 │   │                                                                   │
 │  intermediate  règles métier : doublons, correspondances de codes    │
 │   │                                                                   │
 │  marts         tables prêtes à l’emploi (modèle en étoile)           │
 │                                                                       │
 │  snapshots     photos quotidiennes pour garder l’historique          │
 │  quality       erreurs détectées dans les données                    │
 └───────────────────────────────────────────────────────────────────────┘
        │                                   │
        ▼                                   ▼
 API par rôles (FastAPI)               Power BI
        │                              (mêmes tables, mêmes chiffres)
        ▼
 Interface web React
 (dépôt séparé)

 Dagster lance tout cela automatiquement, à intervalles réguliers.
```

**Une image pour retenir les couches :** une cuisine de restaurant.

| Couche | Dans la cuisine | Dans Analytix |
|---|---|---|
| `raw` | Les ingrédients livrés, rangés tels quels | La copie exacte des sources |
| `staging` | Les ingrédients lavés et épluchés | Les données nettoyées, une table par source |
| `intermediate` | Les préparations (sauces, découpes) | Les règles métier, les sources combinées |
| `marts` | Les plats servis | Les tables utilisées par la plateforme et Power BI |

**Pourquoi des couches ?** Si un chiffre est faux, on peut remonter étape par étape jusqu’à la source pour trouver où l’erreur est apparue. Et on ne touche jamais aux « ingrédients » d’origine.

---

## 7. Le modèle en étoile, expliqué simplement

Dans la couche `marts`, les données sont organisées « en étoile » : une **table de faits** au centre, entourée de **dimensions**.

```
                 dim_date
                    │
   dim_client ── fct_ventes ── dim_article
                    │
                 dim_site
```

- `fct_ventes` contient une ligne par ligne de facture : la quantité, le montant, et les **codes** du client, de l’article, du site et de la date.
- Les dimensions donnent les **descriptions** : nom et ville du client, désignation et catégorie de l’article…

**Pourquoi ce modèle ?**

- Les montants ne sont stockés qu’une fois : pas de risque de les compter deux fois.
- Les dimensions sont **partagées** : le même article a le même code dans les ventes, les achats, le stock et la maintenance. C’est ce qui permet de croiser les services.
- C’est le format que Power BI lit le mieux.

**Avant de créer une table, on écrit toujours son grain** (« une ligne = … »). C’est la meilleure protection contre les doubles comptes.

Ce choix a été comparé à cinq autres architectures (Data Vault, base normalisée, tables larges, tout dans Power BI, fichiers Parquet). La comparaison détaillée est dans le chapitre 8 du cahier des charges.

---

## 8. Quand les données changent

Les données ne sont pas figées : des lignes arrivent, d’autres sont corrigées ou supprimées. Chaque cas a sa réponse.

| Situation | Exemple | Ce qu’on fait |
|---|---|---|
| Petite table | Liste des clients | On la recopie entièrement à chaque fois |
| Grosse table qui peut être modifiée | Écritures comptables | On recopie ce qui a changé depuis la dernière fois (plus les derniers jours, par sécurité), et tout, une fois par semaine |
| Mesures des machines | Courant de l’extrudeuse | On ajoute seulement les nouvelles mesures : une mesure ne change jamais |
| Ligne supprimée dans la source | Facture annulée | On la marque comme supprimée, sans l’effacer |
| Description qui change | Un client change de représentant | On garde l’historique (ancienne et nouvelle valeur, avec leurs dates) quand ça compte pour l’analyse |
| État que la source n’historise pas | Le stock d’un jour donné | On prend une **photo chaque nuit**. Sans elle, l’historique est perdu pour toujours |
| Une application renomme une colonne | Nouvelle version d’une appli | Une alerte se déclenche avant qu’un chiffre soit faussé |
| Une règle de calcul change | Nouvelle définition du CA | Changement dans Git, testé, daté et documenté |

**Principe :** relancer un chargement donne toujours le même résultat. On peut donc rejouer une période sans risque de compter deux fois.

---

## 9. Les outils utilisés et pourquoi

| Rôle | Outil | Pourquoi ce choix |
|---|---|---|
| Lire les sources | Compte SQL Server en **lecture seule** | La protection est garantie par le serveur, pas seulement par notre code |
| Copier les données | **Python** avec **dlt** | Charge des dizaines de tables, en entier ou seulement les nouveautés, sans écrire un script par table |
| Entrepôt de données | **PostgreSQL** | Gratuit, solide, gère la sécurité par ligne, Power BI s’y connecte directement |
| Transformer et tester | **dbt** | Règles écrites en SQL, testées à chaque chargement, documentées automatiquement |
| Lancer et surveiller | **Dagster** | Fonctionne nativement sous Windows, comprend dbt, montre l’état de chaque table |
| API de la plateforme | **FastAPI** (Python) | Même langage que le reste ; applique les droits de chaque rôle |
| Interface | **React** + TypeScript | Interface web moderne, graphiques interactifs. **Dans un dépôt séparé**, qui consomme l’API |
| Analyses libres | **Power BI** | Déjà connu dans l’entreprise ; lit les mêmes tables |
| Versions du code | **Git** + dépôt distant privé | Historique, relecture, sauvegarde |
| Dépendances Python | **uv** | Installe et fige les versions en une commande |

**Ce qu’on n’utilise pas, et pourquoi :**

- **Docker** : non retenu par l’entreprise ; tous les outils choisis fonctionnent sans.
- **Airflow** : ne fonctionne pas directement sous Windows (il faudrait un Linux intégré, WSL2). Dagster fait le même travail.
- **Cloud** (Snowflake, Fabric…) : les données sortiraient de l’entreprise, avec un coût mensuel, alors que toutes les sources sont sur place.

---

## 10. Organisation du dépôt

Organisation prévue ; les dossiers sont créés au fur et à mesure.

```
Jbel_Annour_Analytix/
├── README.md            ce document
├── .env.example         liste des variables à remplir (sans aucun secret)
├── ingestion/           copie des sources vers la couche raw
├── dbt/                 transformations et tests, un dossier par domaine
│   ├── staging/
│   ├── intermediate/
│   └── marts/           finance/, achats/, production/, maintenance/...
├── orchestration/       Dagster : quand et dans quel ordre tout lancer
├── api/                 FastAPI : données et droits par rôle
├── infra/               installation sur le serveur, sauvegardes, scripts de la CI
├── .github/workflows/   CI/CD : contrôles automatiques à chaque pull request
└── docs/                fiches indicateurs, décisions, schémas
    └── confidentiel/    cahier des charges complet, jamais versionné
```

**Règles de nommage des tables :**

| Couche | Format | Exemple |
|---|---|---|
| raw | `raw_<source>.<table d’origine>` | `raw_x3.sinvoice` |
| staging | `stg_<source>__<objet>` | `stg_x3__factures` |
| intermediate | `int_<domaine>__<objet>` | `int_production__postes_dedoublonnes` |
| marts | `dim_<objet>`, `fct_<objet>`, `agg_<objet>` | `dim_article`, `fct_ventes`, `agg_energie_jour` |
| snapshots | `snap_<objet>` | `snap_client` |
| quality | `dq_<contrôle>` | `dq_mesures_manquantes` |

---

## 11. Comment on travaille

### Un service à la fois, de bout en bout

On ne construit pas « toute l’ingestion », puis « tout dbt », puis « toute l’interface ». On livre **un service complet** à chaque étape : copie des données, transformations, tests, endpoints de l’API et Power BI ; la page web correspondante est livrée en parallèle dans le dépôt de l’interface. Chaque étape apporte donc quelque chose d’utilisable, et les erreurs apparaissent tôt.

### Les étapes pour chaque service

1. **Atelier** avec le responsable du service : ses 5 à 10 indicateurs, leur définition, la base qui fait foi.
2. **Fiche indicateur** écrite et validée **avant** de coder (dans `docs/`).
3. **Construction**, avec un commit par partie.
4. **Rapprochement chiffré** avec la source : un test automatique vérifie que nos chiffres retrouvent ceux de la source.
5. **Recette** par le service, puis mise en production.

### Git

```
dev  ──PR──►  main  ──►  production
```

- Deux branches seulement, sans branche `feature`.
- `dev` est la branche **de travail** : on y commite et on y pousse directement ; la CI vérifie chaque push.
- `main` est la version **en production**. On n’y pousse jamais directement : un ensemble validé passe de `dev` à `main` par une pull request, qui déclenche le déploiement.
- Messages de commit en français, à l’impératif : « Ajoute l’extraction des échéances ».
- **Aucun secret dans Git**, jamais : mots de passe et adresses vont dans `.env`, qui est ignoré.

### CI/CD

À chaque push sur `dev` et à chaque pull request vers `main`, GitHub lance des **contrôles automatiques** (fichiers interdits, recherche de secrets, puis au fil du projet : qualité du code, tests Python, tests dbt, tests d’accès par rôle). Une pull request vers `main` dont un contrôle est rouge ne peut pas être fusionnée.

Chaque contrôle, ce qu’il vérifie et pourquoi : **[docs/ci-cd.md](docs/ci-cd.md)**.

### Deux environnements

| Environnement | Où | Base | Usage |
|---|---|---|---|
| Développement | Poste du développeur | `dw_dev` | Essayer, casser, recommencer |
| Production | Serveur de l’entreprise | `dw_prod` | Ce que voient les utilisateurs |

On ne teste jamais directement en production.

### Les garde-fous automatiques

Une version n’est pas publiée si un test échoue : test dbt, rapprochement avec la source ou test d’accès par rôle.

---

## 12. Les règles d’or

1. **On ne modifie jamais une source.** Uniquement des lectures. En cas de doute, on ne lance pas la requête.
2. **On ne copie jamais de données sensibles** : mots de passe, jetons, CIN, RIB, salaires individuels.
3. **On ne met jamais de secret dans Git** : ni mot de passe, ni adresse de serveur.
4. **Un chiffre a une seule définition**, écrite et validée par le service concerné.
5. **On écrit le grain** de chaque table avant de la créer.
6. **On ne corrige pas les sources à la place des services** : Analytix signale les erreurs, le service les corrige dans son application.
7. **On lit sans bloquer** : les machines et Sage X3 tournent en production ; nos lectures ne doivent jamais les ralentir.

---

## 13. Préparer son poste

Outils à installer (tous fonctionnent sous Windows, sans Docker) :

| Outil | Version | À quoi il sert |
|---|---|---|
| Git | récente | Versions du code |
| uv | récente | Installe Python et les bibliothèques |
| Python | 3.12 (installé par uv) | Ingestion, dbt, Dagster, API |
| PostgreSQL | 16 | Data warehouse local de développement |
| ODBC Driver 18 for SQL Server | 18 | Lire Sage X3 et les applications |
| VS Code | récente | Éditeur conseillé |

**Accès à demander** (à l’équipe informatique) :

- un compte **en lecture seule** sur les bases sources ;
- l’accès au réseau de l’entreprise (les serveurs ne sont pas joignables de l’extérieur) ;
- l’accès au dépôt Git distant.

**Démarrage** (commandes complétées au fur et à mesure que le code arrive) :

```powershell
git clone <adresse du dépôt>
cd jbel-annour-analytix-data
git switch dev                                   # branche de travail
copy .env.example .env                           # puis remplir .env avec vos accès
uv sync                                          # installe Python 3.12 et les dépendances figées
uv run python -m ingestion.verifier_connexions   # teste les sources et leurs droits
uv run python -m infra.postgres.initialiser_entrepot --simulation   # affiche le SQL de l'entrepôt
uv run python -m infra.postgres.initialiser_entrepot                # crée dw_dev, ses comptes et schémas
uv run python -m ingestion.x3_ventes --simulation   # contrôles avant copie (droits, colonnes sensibles)
uv run python -m ingestion.x3_ventes                # copie les factures X3 dans raw_x3, puis rapproche
uv run python -m ingestion.x3_finance               # copie incrémentale des échéances et de la comptabilité (--complet chaque semaine)
uv run python -m ingestion.x3_stock                 # stock par article et mouvements (--complet chaque semaine)
uv run python -m ingestion.x3_achats                # demandes, commandes, réceptions, factures fournisseurs
uv run python -m ingestion.usine_magasin            # applications Magasin et espace_magasin (serveur de l'usine)
uv run python -m ingestion.usine_production         # fiches de poste et réalisé par zone (production_2026)
uv run python -m ingestion.usine_machines           # automates : moulage, séchoir, empileuse, four, dépileuse
uv run python -m ingestion.usine_electricite        # 13 compteurs électriques (relevé toutes les 5 minutes)
uv run python -m infra.ci.verifier_types_staging     # types des colonnes nettoyées en staging
cd dbt
uv run --env-file ../.env dbt deps                  # installe les bibliothèques dbt
uv run --env-file ../.env dbt build                 # construit les modèles et lance tous les tests
uv run --env-file ../.env dbt source freshness      # vérifie que les copies sont récentes
cd ..
uv run python -m ingestion.rapprochement --ca       # CA net par année : Sage X3 contre l'entrepôt
uv run python -m ingestion.rapprochement --creances # créances et dettes ouvertes : Sage X3 contre l'entrepôt
uv run python -m ingestion.rapprochement --resultat # résultat par exercice : BALANCE de X3 contre l'entrepôt
uv run python -m ingestion.rapprochement --tresorerie # soldes de trésorerie : BALANCE de X3 contre l'entrepôt
uv run python -m ingestion.rapprochement            # tous les rapprochements
uv run pytest                                    # lance les tests
```

---

## 14. Les pièges connus dans les données

Un premier contrôle, en lecture seule, a déjà trouvé ces problèmes. Ils seront traités dans la couche `intermediate` et suivis dans la couche `quality`.

| Où | Problème | Conséquence |
|---|---|---|
| Sage X3, factures | Le coût de revient enregistré est souvent faux (coût jusqu’à plus de 5 fois le prix de vente) | **Ne jamais calculer la marge avec ce champ** |
| Sage X3, ventes | Les lignes d’avoir sont positives : le signe vient de l’entête de la facture | Sans ce signe, le CA est faux |
| Sage X3, partout | Les vides sont des espaces, les dates absentes valent 1753 ou 1900 | À nettoyer dans `staging` |
| Sage X3, échéances | Près de 14 000 échéances ouvertes depuis plus d’un an | Balance âgée gonflée par des restes anciens |
| Production | Deux bases se recoupent (ancienne et 2026), et des postes sont saisis deux fois | Risque de double comptage |
| Machines | Coupures dans les mesures (jusqu’à 18 jours pour le moulage) | Production et énergie sous-estimées sur ces périodes |
| Électricité | Valeurs de cos φ impossibles, compteur qui recule | Consommations à calculer avec précaution |
| Magasin | Quantités de gasoil saisies comme du texte | À convertir avant tout calcul |
| Pointage | Presque toutes les dates d’embauche valent 1970 | Ancienneté inutilisable |
| Annuaire des utilisateurs | Deux tiers des utilisateurs sans département ni rôle | Les droits ne peuvent pas être attribués automatiquement : **à corriger avant la plateforme** |
| Partout | Aucun lien déclaré entre les tables | Chaque lien est déduit, puis vérifié par un test |

---

## 15. Feuille de route

| Phase | Contenu | Résultat |
|---|---|---|
| 0. Cadrage | Validation du cahier des charges, responsables par service, compte en lecture seule, serveur | Projet prêt à démarrer |
| 1. Socle | Dépôt, entrepôt, ingestion générique, plateforme avec connexion et rôles, page « Qualité des données », Power BI | Ventes en ligne pour les premiers utilisateurs |
| 2. Finance | Créances, balance âgée, trésorerie, compte de résultat | Module Finance |
| 3. Achats, magasin, stock | Circuit d’achat, budgets, sorties, stock valorisé, gasoil | Modules Achats et Stock |
| 4. Production et machines | Postes, objectifs, machines, cadence | Module Production |
| 5. Énergie et qualité | Électricité, combustibles, contrôles qualité | Modules Énergie et Qualité |
| 6. Maintenance | Pannes, réparations, pièces, ordres de travail | Module Maintenance |
| 7. Coût de revient et direction | Coût par tonne, marge, vue groupe | Tableau de bord Direction |
| 8. RH | Effectifs, pointage, absentéisme (agrégés) | Module RH |

**À faire dès la phase 1 :** commencer les photos quotidiennes du stock et des créances. Chaque jour sans photo est un jour d’historique perdu.

---

## 16. Questions encore ouvertes

- Quelle base fait foi pour la production, la maintenance, le magasin et le pointage ?
- La société « Jbel Annour » du dossier groupe est-elle la même que celle de BASE1 ? Quelles opérations sont saisies dans chaque dossier ?
- Quel serveur hébergera la plateforme ? L’entreprise a-t-elle un annuaire Active Directory pour les connexions ?
- Quelles licences Power BI sont disponibles ?
- Quels indicateurs RH la direction autorise-t-elle ?

---

## 17. Pour aller plus loin

| Document | Contenu | Où |
|---|---|---|
| **Cahier des charges** (confidentiel) | Détail de chaque base, anomalies chiffrées, sécurité, exigences, choix des outils et de l’architecture justifiés, méthode, planning, lexique | `docs/confidentiel/`, dossier exclu de Git : à demander au responsable du projet |
| Projet pilote « Analyse des ventes » | Première version du pipeline (Sage X3 → PostgreSQL → dbt → Dagster) et du tableau de bord des ventes, qui a servi à valider les choix | Dépôts `Analyse_vente` et `Dashboard_ventes` |
| Documentation dbt | Description de chaque table et de chaque colonne | Générée par `dbt docs` (dès la phase 1) |

Une question sur ce document ? Notez-la dans la [partie 16](#16-questions-encore-ouvertes) pour qu’elle soit tranchée.
