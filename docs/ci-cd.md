# Branches, CI/CD et contrôles automatiques

Ce document explique comment le code passe du poste du développeur à la production, et **chaque contrôle automatique** qui le vérifie en chemin : ce qu'il fait, et pourquoi il existe.

---

## 1. Les branches

```
dev  ──push──►  CI      (travail quotidien, contrôlé à chaque push)
 │
 └──PR──►  main  ──►  production
```

Le projet n'utilise que **deux branches**, sans branche `feature`.

| Branche | Rôle | Qui écrit dessus |
|---|---|---|
| `dev` | La branche **de travail** : tous les commits du quotidien arrivent ici | Le développeur, directement (`git push`) |
| `main` | La version **en production**. Elle fonctionne toujours. | Personne directement : uniquement par pull request depuis `dev` |

**Pourquoi deux branches ?** `dev` sert de sas : on y travaille, la CI y vérifie chaque push, et on peut y casser quelque chose sans conséquence. On ne passe en production (`main`) qu'un ensemble cohérent, validé par le service concerné.

**Pourquoi pas de branche `feature` ?** Avec une à deux personnes sur le projet, les branches `feature` ajoutent des fusions sans apporter grand-chose. La contrepartie : `dev` peut être temporairement rouge, et c'est à corriger avant tout passage en production.

### Le déroulé

1. Travailler sur `dev`, à jour :
   ```powershell
   git switch dev
   git pull
   ```
2. Faire un commit par partie (messages en français, à l'impératif), puis pousser :
   ```powershell
   git push
   ```
3. La CI se lance sur `dev`. **Si elle est rouge, on corrige tout de suite**, par un nouveau commit sur `dev`.
4. Quand un ensemble est prêt (fin d'un module, recette faite) : **pull request `dev` → `main`** sur GitHub. La CI se relance ; la fusion n'est possible que si elle est verte. La fusion déclenche ensuite le déploiement en production (CD, voir partie 4).
5. Après la fusion, `dev` et `main` sont identiques ; on continue sur `dev`.

---

## 2. Protéger les branches sur GitHub

À faire une fois, dans **Settings → Branches → Add branch ruleset** (ou *Branch protection rules*).

**Pour `main` :**

| Règle | Pourquoi |
|---|---|
| *Require a pull request before merging* | Personne ne pousse directement en production : tout passe par `dev` |
| *Require status checks to pass* → cocher **Fichiers interdits** et **Recherche de secrets** | La fusion est bloquée si un contrôle échoue |
| *Require branches to be up to date before merging* | Les contrôles tournent sur le code tel qu'il sera après la fusion |
| *Block force pushes* et *Restrict deletions* | L'historique de production ne peut être ni réécrit ni supprimé |

**Pour `dev` :** seulement *Block force pushes* et *Restrict deletions*. Les push directs restent autorisés, puisque c'est la branche de travail.

Les contrôles n'apparaissent dans la liste qu'après leur **première exécution**. Poussez donc `dev` une première fois avant de régler la protection de `main`.

---

## 3. La CI : les contrôles automatiques

La CI (*intégration continue*) est définie dans [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). Elle tourne sur les serveurs de GitHub à chaque pull request et à chaque push sur `dev` ou `main`.

**Limite importante :** les serveurs de GitHub **ne peuvent pas joindre le réseau de l'entreprise**. La CI ne lit donc jamais Sage X3 ni les bases de l'usine. Elle teste le code avec des données d'essai ; les tests sur les vraies données tournent dans l'entrepôt, à chaque chargement, lancés par Dagster.

### Contrôles en place

#### Fichiers interdits (`infra/ci/verifier_depot.py`)

Ce script lit la liste des fichiers suivis par Git et échoue s'il trouve :

| Contrôle | Ce qu'il détecte | Pourquoi |
|---|---|---|
| `[secret]` | Un fichier `.env`, `.env.prod`… (seul `.env.example` est permis) | Ces fichiers contiennent les mots de passe des serveurs. Règle d'or n° 3 |
| `[confidentiel]` | Un fichier de `docs/confidentiel/` ou `exploration/` | Le cahier des charges décrit des serveurs et des failles de sécurité ; les inventaires décrivent chaque table |
| `[donnees]` | Un `.csv`, `.xlsx`, `.parquet`, `.bak`… hors de `dbt/seeds/` | Une extraction de données posée par erreur dans le dossier peut contenir des données personnelles (loi 09-08). Règle d'or n° 2 |
| `[taille]` | Un fichier de plus de 5 Mo | Presque toujours une extraction ou un fichier généré ; un dépôt lourd est lent à cloner, et on ne peut plus l'alléger après coup |
| `[adresse]` | Une adresse IP de réseau privé (`192.168.…`, `10.…`, `172.16-31.…`) dans un fichier texte | Les adresses des serveurs vont dans `.env`, jamais dans le code. Le message d'erreur donne le fichier et la ligne, sans afficher l'adresse |

À lancer en local avant de pousser :

```powershell
python infra/ci/verifier_depot.py
```

Le `.gitignore` empêche déjà d'ajouter ces fichiers par erreur. Ce contrôle est le **second filet** : il attrape un `git add -f`, un `.gitignore` modifié ou un fichier mal nommé.

#### Recherche de secrets (gitleaks)

[gitleaks](https://github.com/gitleaks/gitleaks) parcourt **tout l'historique Git** à la recherche de mots de passe, clés d'API, jetons et chaînes de connexion, d'après des centaines de motifs connus.

| Point | Explication |
|---|---|
| Pourquoi tout l'historique | Supprimer un mot de passe dans un nouveau commit ne l'efface pas : il reste lisible dans les commits précédents |
| Pourquoi en plus du script | Le script repère des **fichiers** interdits ; gitleaks repère un **secret à l'intérieur** d'un fichier autorisé, par exemple un mot de passe copié dans un script Python |
| `--redact` | La valeur trouvée n'est jamais affichée dans les journaux de la CI, qui sont lisibles par tous ceux qui ont accès au dépôt |

**Si gitleaks trouve un secret :** le retirer du code ne suffit pas. Il faut considérer le mot de passe comme connu, **le faire changer** par l'équipe informatique, puis nettoyer l'historique.

#### Code Python (uv, ruff, pytest)

| Contrôle | Ce qu'il vérifie | Pourquoi |
|---|---|---|
| **Dépendances figées** (`uv sync --locked`) | Le fichier `uv.lock` correspond exactement à `pyproject.toml` | Tout le monde (poste, CI, serveur) installe les mêmes versions, à la lettre près. Si quelqu'un ajoute une bibliothèque sans mettre à jour le verrou, la CI échoue |
| **Style et erreurs** (`ruff check`) | Imports inutiles, variables jamais utilisées, syntaxe dépassée, pièges connus de Python | Ces erreurs sont détectées avant l'exécution, sans serveur. Un code homogène se relit plus vite |
| **Mise en forme** (`ruff format --check`) | Le code est mis en forme selon une seule règle (indentation, guillemets, longueur des lignes) | Les relectures portent sur le fond, pas sur des espaces. Corriger en local avec `uv run ruff format` |
| **Tests unitaires** (`pytest`) | Les fonctions Python donnent le bon résultat sur des cas connus | Voir le détail des tests ci-dessous |

**Les tests en place :**

| Fichier | Ce qu'il teste | Pourquoi c'est important |
|---|---|---|
| `tests/test_config.py` | Chaque source lit ses variables avec son préfixe (`X3_`, `JBELRH_`, `USINE_`), sans prendre celles d'une autre | Se connecter au mauvais serveur avec le mauvais compte serait silencieux |
| | Le mot de passe n'apparaît jamais dans l'affichage de la configuration | Un `print` ou un message d'erreur ne doit jamais divulguer un mot de passe dans un terminal ou un journal |
| | Une valeur vide (`X3_PORT=`) vaut « non renseignée » | Le modèle `.env.example` laisse des champs vides |
| | Un compte SQL sans mot de passe, ou un environnement inconnu (`production` au lieu de `prod`), est refusé dès le démarrage | Une erreur de configuration doit arrêter le programme tout de suite, avec un message clair, et non échouer plus loin |
| `tests/test_sqlserver.py` | La connexion est demandée en lecture seule, chiffrée, et identifiée par le nom « Jbel Annour Analytix » | L'équipe informatique doit pouvoir reconnaître nos sessions sur ses serveurs |
| | Serveur avec port, instance nommée (`serveur\INSTANCE`), choix de la base, authentification Windows | Ce sont les cas réels des trois serveurs sources |
| | Un mot de passe contenant `;`, `}`, `=` ou une espace est protégé | Sans protection, un `;` coupe la chaîne de connexion : la connexion échoue, ou pire, la suite est lue comme un autre paramètre |
| | Le contrôle des droits accepte un compte en lecture seule et **refuse** un compte administrateur (`sa`, `sysadmin`, `db_owner`) ou qui peut écrire (`db_datawriter`, `INSERT`, `UPDATE`, `DELETE`…) | Règle d'or n° 1 : on ne modifie jamais une source. Cette protection doit venir du serveur, et on vérifie qu'elle est bien là |
| | Un compte qui peut écrire est **refusé par défaut**, et **toléré** seulement avec une dérogation explicite `<SOURCE>_COMPTE_ADMIN_ACCEPTE=yes` (avertissement à chaque exécution). La dérogation d'une source ne s'applique pas aux autres | L'entreprise a décidé de lire le serveur de l'usine avec le compte `sa`, en dev comme en prod. La dérogation reste visible et limitée à cette source : un compte administrateur ajouté par erreur sur Sage X3 serait refusé |
| | Un droit d'écriture accordé **sur le schéma du dossier X3** (`BASE1`) est refusé | Dans Sage X3, un compte peut écrire dans un dossier sans être membre d'aucun rôle : le contrôle des rôles seul ne le verrait pas |

| `tests/test_entrepot_plan.py` | Le script d'initialisation refuse toute base autre que `dw_dev`, `dw_prod`, `dw_test` | Le PostgreSQL du poste héberge d'autres projets (`agent_ai`, `chatbot_site`, le pilote `dw_ventes`) : une faute de frappe dans `.env` ne doit jamais les modifier |
| | Il refuse tout rôle dont le nom ne commence pas par `analytix_` | Le script change le mot de passe des rôles qu'il gère : il ne doit jamais toucher `postgres` ni `dw_ventes` |
| | Une relance ne recrée rien (idempotence) | On peut relancer le script après un changement de droits, sans risque |
| | Aucun compte n'est administrateur ; l'API est en lecture seule forcée par le serveur, avec un délai maximal par requête | Une faille dans l'API ne doit permettre ni d'écrire ni de bloquer l'entrepôt avec une requête sans fin |
| | Le groupe de lecture ne reçoit que `USAGE` et `SELECT`, et seulement sur `marts` | Les données non nettoyées (`raw`, `staging`) ne sortent jamais vers l'API ni Power BI |
| | Les mots de passe ne s'affichent jamais et sont passés en paramètre, jamais collés dans le SQL | Ni fuite dans le terminal, ni injection SQL |

#### Entrepôt PostgreSQL (job « Entrepôt PostgreSQL »)

La CI démarre un **PostgreSQL 16 jetable** (détruit à la fin du job), y lance le script d'initialisation **deux fois**, puis vérifie les droits réels de chaque compte (`tests/test_entrepot_acces.py`) :

| Test | Pourquoi |
|---|---|
| Les 5 schémas existent ; le compte de chargement peut créer un schéma `raw_…` | L'ingestion crée elle-même un schéma par source |
| L'API lit une table de `marts` **créée après** l'initialisation | Vérifie les droits par défaut : chaque table que dbt créera sera lisible sans intervention |
| L'API ne peut ni insérer, ni créer de table | Lecture seule forcée par le serveur |
| L'API ne peut pas lire `staging` | Seule la couche `marts` est exposée |
| Même en désactivant la lecture seule dans sa session, l'API ne peut pas écrire | Deux protections indépendantes : la lecture seule **et** les droits |

Ces tests ne tournent que sur une base nommée `dw_test`, jamais sur `dw_dev` ni `dw_prod`. Les mots de passe du job n'existent que dans ce conteneur jetable.

**Ce que la CI ne teste pas :** la vraie connexion aux serveurs, qu'elle ne peut pas joindre. Elle se vérifie sur le poste, avec :

```powershell
uv run python -m ingestion.verifier_connexions
```

### Contrôles prévus, ajoutés au fil des étapes

| Étape | Contrôle | Ce qu'il vérifiera | Pourquoi |
|---|---|---|---|
| Entrepôt (dbt) | **dbt parse / compile** | Les modèles SQL sont valides et leurs dépendances cohérentes | Une référence à une table inexistante est détectée avant le déploiement |
| Entrepôt (dbt) | **Tests unitaires dbt** | Une règle métier donne le bon résultat sur des lignes d'essai (ex. signe des avoirs, dates 1753) | Les pièges connus des données (README, partie 14) restent corrigés à chaque modification |
| Entrepôt (dbt) | **dbt build sur une base PostgreSQL vide** | Toutes les tables se construisent et tous les tests passent, sur des données d'essai | Vérifie la chaîne complète sans accès aux vraies sources |
| Entrepôt (dbt) | **Contrats des tables `marts`** | Colonnes et types des tables lues par Power BI et l'API inchangés | Une colonne renommée ne doit jamais casser un rapport sans prévenir |
| Entrepôt (dbt) | **Colonnes sensibles** | Aucune colonne nommée CIN, RIB, salaire, mot de passe, jeton… dans les modèles | Critère d'acceptation n° 4 du cahier des charges |
| API | **Tests d'accès par rôle** | Pour chaque rôle, l'API refuse toute donnée hors de son périmètre | Critère d'acceptation n° 3 : un représentant ne voit jamais les clients d'un autre |
| API | **Schéma OpenAPI** | Le contrat de l'API n'a pas changé sans le signaler | L'interface web, dans un autre dépôt, en dépend |

Chaque contrôle sera expliqué ici au moment de son ajout.

---

## 4. Le CD : le déploiement

Le CD (*déploiement continu*) installe automatiquement la nouvelle version sur le serveur après une fusion dans `main`.

**Ce qui est prévu :**

- Le serveur de production est **interne** : GitHub ne peut pas s'y connecter. On installe donc sur ce serveur un **runner GitHub auto-hébergé** : un petit service Windows qui va lui-même chercher le travail chez GitHub (connexion sortante uniquement, aucun port à ouvrir).
- À chaque fusion dans `main`, ce runner : récupère le code, installe les dépendances (`uv sync`), lance `dbt build` sur `dw_prod`, puis redémarre les services Dagster et API.
- Les mots de passe de production restent dans le `.env` du serveur, jamais dans GitHub.
- Si une étape échoue, la version précédente reste en service.

**Quand :** dès que le serveur de production est choisi (question ouverte, README partie 16). En attendant, le déploiement se fait à la main en suivant `infra/`.
