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

| `tests/test_ingestion_x3.py` | Une colonne dont le nom ressemble à une donnée sensible (`PASS`, `PWD`, `TOKEN`, `CIN`, `RIB`, `IBAN`, `BAN_`, `SALAIRE`…) **arrête le chargement** tant qu'elle n'a pas été exclue ou autorisée explicitement | Règle d'or n° 2. En cas de doute on ne copie rien : la décision est écrite dans le code, avec sa raison (ex. `BPCINV_0` = client facturé, pas un CIN) |
| | Une colonne exclue n'est jamais demandée à la source | La donnée sensible ne quitte même pas le serveur Sage X3 |
| | Une colonne décidée qui a disparu de la source est signalée | Un changement de structure dans Sage X3 ne passe pas inaperçu |
| | La banque de paiement (`PAYBAN_0`) n'est jamais copiée | Donnée bancaire |
| | Le rapprochement détecte une ligne manquante, un écart de montant d'un centime ou plus, un doublon de clé ; il tolère moins d'un centime | Critère d'acceptation n° 1 : écart inférieur à 0,01 MAD, nul pour les comptages |
| | Une liste fermée ne copie que les colonnes choisies ; elle reste soumise au contrôle des colonnes sensibles ; la fiche client ne contient ni CIN ni banque | Une colonne ajoutée plus tard dans X3 n'entre jamais sans décision |
| | Une table incrémentale dont la date de modification ou la clé ne serait pas copiée est refusée ; les échéances sont copiées en incrémental, avec leur clé complète | Sans la date, la copie ne reprendrait pas ; sans la clé, la fusion créerait des doublons |
| | La requête de rapprochement additionne les 28 colonnes de la BALANCE (à-nouveaux et périodes), registre général seulement ; les écritures sont copiées sans libellé ni nom de tiers | Une période oubliée fausserait le résultat de référence ; un libellé peut contenir un nom de personne |
| | Les soldes sont comparés compte par compte (deux écarts qui se compensent restent visibles) ; la `BALANCE` est lue sur ses lignes de total (site et tiers vides) | Un total juste peut cacher deux comptes faux ; la `BALANCE` double les comptes suivis par tiers |
| `tests/test_photos_dbt.py` | **Chaque** photo quotidienne (dossier `dbt/models/snapshots`) a `full_refresh=false`, est incrémentale et remplace seulement la photo du jour | Une nouvelle photo oubliée sans cette protection serait effacée par un `--full-refresh` : le test l'interdit dès l'ajout |
| `infra/ci/verifier_types_staging.py` (outil, et son test) | Chaque macro de nettoyage (`texte_x3`, `date_x3`…) s'applique à une colonne du bon type dans raw | Dans X3, une même colonne est un texte dans une table et un nombre dans une autre : l'outil liste tout d'un coup, avant la construction dbt |
| `tests/test_yaml_dbt.py` | Les YAML de dbt sont valides, et aucune description n'a été coupée par une virgule dans `{ … }` | Une description coupée crée une clé fantôme sans aucune erreur visible |
| `tests/test_sqlserver.py` | La requête de lecture des données envoyée par dlt contient `WITH (NOLOCK)` | Règle d'or n° 7 : lire Sage X3 sans poser ni attendre de verrou |

**Le rapprochement sur les vraies données** ne peut pas tourner dans la CI (pas d'accès à Sage X3). Il est lancé automatiquement à la fin de chaque copie, sur le poste ou le serveur :

```powershell
uv run python -m ingestion.x3_ventes          # copies raw_x3 contre X3 (lignes, montants, doublons)
uv run python -m ingestion.rapprochement --ca # CA net par année : Sage X3 contre marts.fct_ventes
uv run python -m ingestion.rapprochement --creances # restes à payer ouverts, clients et fournisseurs
uv run python -m ingestion.rapprochement --resultat # résultat par exercice : BALANCE de X3 contre l'entrepôt
uv run python -m ingestion.rapprochement --tresorerie # soldes de trésorerie, compte par compte
uv run python -m ingestion.rapprochement --stock # stock valorisé par site
uv run python -m ingestion.rapprochement --achats # dépense d'achat par année (lignes de factures)
```

Le rapprochement du CA calcule le même indicateur des deux côtés, mais par deux chemins : les **entêtes** dans Sage X3, les **lignes** dans l'entrepôt. Écart toléré : moins de 0,01 MAD par année (critère d'acceptation n° 1).

#### Projet dbt (job « Projet dbt »)

| Contrôle | Ce qu'il vérifie | Pourquoi |
|---|---|---|
| `dbt deps` | Les bibliothèques dbt s'installent dans la version figée (`package-lock.yml`) | Même principe que `uv.lock` : partout les mêmes versions |
| `dbt parse` | Tout le projet se lit sans erreur : SQL et Jinja valides, chaque `ref()` et `source()` pointe vers un modèle qui existe, chaque test est bien écrit | Une faute de frappe dans un nom de modèle est détectée avant la fusion, sans avoir besoin de l'entrepôt |

#### Les tests dbt sur les données (à chaque `dbt build`)

Ces tests tournent **sur les vraies données**, sur le poste aujourd'hui, et à chaque chargement lancé par Dagster plus tard. Un test en échec bloque les modèles qui en dépendent.

| Modèle | Test | Ce qu'il vérifie | Pourquoi |
|---|---|---|---|
| `stg_x3__factures` | `unique`, `not_null` sur `numero_facture` | Un document = une ligne | Le grain écrit dans le modèle est respecté : pas de double comptage |
| | `accepted_values` sur `type_facture` | Seulement FAC, AVF, AVR, PRF | Un nouveau type de document dans X3 doit être décidé avant d'entrer dans le CA |
| | `accepted_values` sur `signe` | Seulement 1 ou -1 | Le CA est calculé avec ce signe |
| | `accepted_values` sur `devise` (avertissement) | MAD | Une autre devise n'est pas une erreur, mais les montants ne s'additionnent plus directement |
| | `not_null` sur société, site, client, date, montants | Champs indispensables renseignés | Une facture sans date ou sans client disparaîtrait des analyses |
| | `assert_x3_signe_coherent_avec_type` | Avoir ⇔ signe -1, facture ou pro forma ⇔ signe 1 | Un avoir avec le signe 1 serait **ajouté** au CA au lieu d'en être retiré |
| `stg_x3__lignes_facture` | Unicité de (`numero_facture`, `numero_ligne`) | Une ligne de document = une ligne | Grain respecté |
| | `relationships` vers `stg_x3__factures` | Chaque ligne a son entête | Pas de ligne orpheline, qui serait comptée par article mais pas par client |
| | `not_null` sur `representant` (avertissement) | Représentant renseigné | 63 lignes sans représentant : elles échapperaient au filtre « mes clients ». Signalé, pas bloquant |
| Les deux | `assert_x3_total_lignes_egal_entete` | Pour chaque document, HT des lignes = HT de l'entête (au centime) | Les analyses par article et par client doivent donner le même CA |
| | Test unitaire `nettoyage_des_vides_deguises_x3` | Sur des lignes d'essai : espaces retirés, `' '` → vide, dates 1753 / 1900 → vide, entête technique sans numéro retiré | Prouve que le nettoyage fonctionne sur les pièges connus de X3, indépendamment des données du moment |
| `stg_x3__clients`, `stg_x3__articles` | `unique`, `not_null` sur le code | Un client, un article = une ligne | Les dimensions ne doivent jamais dupliquer une vente |
| | `not_null` sur `nom_client` (avertissement) | Raison sociale renseignée | 9 fiches sans nom (inactives, sans vente) : signalé à l'ADV, pas bloquant |
| `dim_date`, `dim_client`, `dim_article`, `fct_ventes` | **Contrat** (`contract: enforced`) | Colonnes et types exactement ceux déclarés ; clé primaire posée dans PostgreSQL | Ce sont les tables lues par l'API et Power BI : une colonne renommée ou un type changé **bloque la construction** au lieu de casser un rapport en silence |
| `dim_client`, `dim_article` | `assert_dimensions_une_ligne_inconnue` | Une et une seule ligne « Inconnu » | Une vente sans client reste comptée ; jamais comptée deux fois |
| `fct_ventes` | Unicité (`numero_facture`, `numero_ligne`) | Une ligne de facture = une ligne | Grain respecté |
| | `relationships` vers `dim_date`, `dim_client`, `dim_article` | Chaque vente trouve son jour, son client, son article | Une jointure ne fait jamais disparaître une vente des totaux |
| | `accepted_values` sur `type_facture` | FAC, AVF, AVR (jamais PRF) | Les pro forma n'entrent jamais dans le CA |
| | Test unitaire `ventes_avoir_negatif_et_pro_forma_exclue` | Sur des lignes d'essai : un avoir devient négatif, une pro forma disparaît | Les deux règles qui font le CA net, prouvées indépendamment des données |
| | `assert_ventes_ca_egal_entetes` | CA par année depuis les **lignes** (fct_ventes) = CA depuis les **entêtes** (staging), au centime | Deux chemins indépendants vers le même chiffre : une jointure qui perd ou duplique des lignes est détectée |
| `stg_x3__echeances` | Unicité (type, pièce, ligne, échéance) | Une échéance = une ligne | La copie incrémentale fusionne par cette clé : un doublon signalerait une fusion ratée |
| | `accepted_values` sur type de tiers (1, 2) et signe (1, -1) | Valeurs connues seulement | Le reste à payer et le partage clients / fournisseurs en dépendent |
| `fct_echeances` | **Contrat**, clé primaire | Colonnes et types figés | Table lue par l'API et Power BI |
| | `relationships` vers `dim_client` (avertissement) | Chaque échéance client a sa fiche client | Les créances doivent se lire par client |
| | `accepted_values` sur `tranche_retard` | Les 7 tranches de la fiche indicateur, rien d'autre | Une tranche mal écrite disparaîtrait de la balance âgée |
| | Test unitaire `echeances_reste_signe_et_tranches` | Date du jour figée au 30/06/2026 : reste à payer signé, avoir négatif, échéance soldée sans tranche, bornes 30 / 31 jours | La balance âgée est juste aux limites des tranches, quel que soit le jour où le test tourne |
| `snap_echeances_ouvertes` | Unicité (jour, échéance) | Une photo par échéance et par jour | Relancer dbt dans la journée remplace la photo du jour sans la doubler |
| | `full_refresh=false` | Même `--full-refresh` ne reconstruit pas la table | Les photos passées ne se recalculent pas : les effacer serait une perte définitive |
| `stg_x3__lignes_ecriture` | `assert_x3_paie_sans_salarie_identifiable` | Aucune ligne des comptes de personnel (617, 443, 3431) ne porte de tiers | Règle d'or n° 2 : si la paie était un jour comptabilisée salarié par salarié, ce test **bloquerait la chaîne** avant que des salaires individuels ne soient exposés. Il ne renvoie que des comptages, jamais un montant |
| | Unicité (pièce, ligne, registre) ; `accepted_values` registre (1, 2) et sens (1, -1) | Grain et valeurs connues | La fusion incrémentale et le calcul débit / crédit en dépendent |
| `fct_ecritures` | **Contrat**, clé primaire ; `relationships` vers `dim_compte` | Chaque ligne a son compte | Une ligne sans compte disparaîtrait du CPC |
| | `assert_ecritures_equilibrees` | Chaque pièce : débits = crédits, au centime | Partie double : une pièce déséquilibrée dans l'entrepôt signalerait une ligne perdue ou doublée |
| | `assert_exercices_clotures_soldes` | Un exercice clôturé a ses classes 6 et 7 à zéro, clôture comprise | Une pièce de clôture manquante, ou une écriture perdue ou doublée, est détectée ; garantit que le résultat hors clôture est le résultat de l'exercice |
| `dim_compte` | `accepted_values` sur `nature` | charge, produit, bilan | Le CPC ne lit que les charges et les produits |
| `agg_compte_de_resultat_mois` | Unicité (mois, société, compte, exercice) ; rubrique renseignée | Un compte par mois ; chaque compte de classe 6 ou 7 a sa rubrique | Un compte sans rubrique sortirait du CPC présenté par rubrique |
| `fct_ecritures` | Exercice déduit de la **date** comptable | — | Une pièce datée du 04/04/2025 était saisie sur l'exercice 2024 : se fier au champ « exercice » la mettait dans la mauvaise année (écart de 209 405,34 MAD avec la `BALANCE`) |
| `stg_x3__lignes_ecriture` | `assert_x3_exercice_coherent_avec_date` (avertissement) | Lignes dont l'exercice saisi contredit la date | Liste les pièces à faire corriger dans Sage X3 |
| | `assert_x3_ecritures_pas_dans_le_futur` (avertissement) | Écritures datées après le jour du chargement | 16 lignes datées de 2027 (cahier des charges, 5.2) |
| `stg_x3__reglements` | `unique`, `not_null` ; `accepted_values` sur le sens (1, 2) | Un règlement = une ligne | Encaissement positif, décaissement négatif |
| `fct_reglements` | **Contrat**, clé primaire ; `accepted_values` sur `sens` | encaissement, décaissement | Table lue par l'API et Power BI |
| `agg_tresorerie_jour` | **Contrat** ; unicité (jour, exercice, compte) ; familles connues | Un solde par compte et par jour | Le cumul repart à chaque exercice : les à-nouveaux reportent déjà le solde |
| `stg_x3__stock_articles` | Unicité (article, site) ; `relationships` vers les articles | Un article sur un site = une ligne | Le stock valorisé ne compte pas deux fois un article |
| `stg_x3__mouvements_stock` | Unicité (clé de STOJOU) | Un mouvement = une ligne | La copie incrémentale fusionne par cette clé |
| | `assert_x3_stock_quantite_valeur_meme_signe` | La valeur a le signe de la quantité | Une sortie de valeur positive serait comptée comme une entrée |
| `fct_stock_article`, `fct_mouvements_stock` | **Contrats**, clés primaires ; `relationships` vers `dim_article` | Colonnes figées, articles connus | Tables lues par l'API et Power BI |
| `fct_stock_article` | `assert_stock_cmup_plausible` (avertissement) | Articles qui pèsent plus de 5 % du stock de leur site | 10 articles (en-cours au CMUP aberrant) font 535 M MAD sur 599 M MAD |
| `snap_stock_jour` | Unicité (jour, article, site) ; `full_refresh=false` | Une photo par article et par jour, jamais effacée | Le stock passé ne se recalcule pas de façon fiable |
| Achats (staging) | Unicité de chaque table à sa clé (DA, ligne de DA, lien DA → commande, commande, ligne de commande, réception, facture, ligne de facture, fournisseur) ; `relationships` lignes → entêtes et commandes → fournisseurs | Chaque document et chaque ligne une seule fois ; aucun orphelin | Le circuit relie quatre documents : un doublon ou un orphelin fausserait délais et dépenses |
| | `assert_x3_da_montant_plausible` (avertissement) | Lignes de DA de plus de 100 M MAD | 85 lignes à prix fictif (500 000 MAD) totalisent 6 171 milliards MAD |
| | `assert_x3_facture_fournisseur_entete_egal_lignes` (avertissement) | Factures dont l'entête ne correspond pas aux lignes | 22 factures : la comptabilité (entête) et l'analyse par article (lignes) divergent pour elles |
| `dim_fournisseur`, `fct_cycle_achat`, `fct_achats_factures` | **Contrats**, clés primaires ; `relationships` vers `dim_fournisseur` et `dim_article` | Colonnes figées, fournisseurs et articles connus | Tables lues par l'API et Power BI |
| Magasin (staging usine) | Unicité des identifiants ; `relationships` des articles de sortie vers Sage X3 ; décisions connues (APPROVED, REJECTED) | Une sortie, un bon, une DA = une ligne ; articles connus de X3 | Les sorties se croisent avec le stock et les achats par la clé article |
| | `assert_magasin_gasoil_quantite_plausible` (avertissement) | Bons négatifs ou de plus de 2 000 L | 9 bons aberrants (jusqu'à -449 595 L) fausseraient la consommation |
| `fct_sorties_magasin`, `fct_gasoil`, `fct_demandes_achat_usine`, `fct_depassements_budget` | **Contrats**, clés primaires ; `relationships` vers `dim_article` | Colonnes figées | Tables lues par l'API et Power BI |
| Ingestion de l'usine | Contrôle du compte avant lecture : `sa` toléré par dérogation, avec avertissement | Lecture seule, sans verrou | Dérogation du 25/11/2026 (cahier des charges 5.4) |
| Production (staging usine) | Unicité des identifiants ; `relationships` lignes → fiches (avertissement) | Une fiche, une ligne = une ligne | 20 lignes sans fiche, signalées |
| `int_production__fiches_dedoublonnees` | **Test unitaire `dedoublonnage_une_fiche_retenue_par_poste`** | Trois saisies du même poste : seule la plus récente est retenue ; fiche supprimée et fiche sans équipe exclues | La règle qui évite de compter un poste plusieurs fois (jusqu'à 20 saisies du même poste) |
| | Unicité (date, shift, équipe) **parmi les fiches retenues** | Jamais deux fiches retenues pour le même poste, sur les vraies données | Sans elle, le réalisé du monobloc serait surévalué de 15 % |
| `fct_production_poste`, `fct_fiches_poste` | **Contrats**, clés primaires ; zones connues ; unicité (poste, zone) en avertissement | Colonnes figées, 5 zones | Tables lues par l'API et Power BI |
| `fct_machines_jour` | **Test unitaire `machines_total_du_jour_est_le_dernier_releve`** | Trois relevés cumulés (267, 583, 935 t) donnent 935 t pour le jour, pas 1 785 t | Les compteurs des automates sont cumulés depuis le début de la journée : additionner les relevés compterait la production deux à trois fois |
| `stg_machines__releves` | **Test unitaire `duree_automate_en_heures`** | « 2: 1:53 » vaut 2,0314 h ; « encours » devient vide | Les automates écrivent des durées en texte, avec des espaces à la place des zéros |
| Machines | `assert_machines_compteur_cumule_croissant` (avertissement) | Un relevé plus grand que le dernier de la journée | Une remise à zéro du compteur en cours de journée fausserait le total du jour |
| | `assert_machines_cycle_wagon_plausible` (avertissement) | Wagons sortis avant d'entrer ou restés plus de 24 h | Erreurs d'horodatage (cahier des charges, 5.2) |
| `fct_machines_jour`, `fct_moulage_quart_heure`, `agg_moulage_coupures`, `fct_wagons` | **Contrats**, clés primaires ; machines connues | Colonnes figées | Tables lues par l'API et Power BI |
| `fct_electricite_jour` | **Test unitaire `electricite_la_valeur_veille_va_au_jour_precedent`** | Les 19 362 kWh affichés le 25/11 sont rangés au 24/11 ; une valeur négative (-589 773) est écartée ; l'index n'est pas utilisé | Le compteur donne la consommation de la veille : la ranger au jour de lecture décalerait tout d'un jour. L'index recule plus de 600 fois par an |
| `stg_electricite__releves` | Couple compteur + relevé unique | Un relevé copié deux fois | Les 13 compteurs sont réunis dans une seule vue : un doublon doublerait le jour |
| `stg_production__consommations` | Rapport unique et non vide | Un rapport saisi deux fois | Les consommations saisies en texte servent de contrôle des compteurs |
| `fct_electricite_jour`, `agg_energie_jour` | **Contrats**, clés primaires ; compteurs et niveaux connus ; `electricite_complete` jamais vide | Un compteur inconnu, un jour en double | Le kWh par tonne n'est calculé que les jours où les deux transformateurs sont mesurés |
| `stg_production__pesees_briques` | **Test unitaire `pesees_texte_en_kg_une_ligne_par_brique`** | « 3,382 » vaut 3,382 kg ; une case vide, « 0 » ou « néant » n'est pas une pesée ; Monobloc devient « mouleuse » | Les poids sont saisis en texte dans 8 colonnes : une conversion ratée fausserait toutes les moyennes |
| `fct_pesees_briques` | **Test unitaire `pesee_aberrante_exclue_de_la_moyenne`** | Trois briques à 3,4 kg et une saisie « 3382 » : la saisie est comptée aberrante, la moyenne reste 3,4 kg | Une seule virgule oubliée multiplierait la moyenne du jour par 250 |
| `fct_chariots_qualite` | **Test unitaire `chariot_prend_le_defaut_le_plus_grave`** | Mineur + majeur donne « défaut majeur » ; tout en bleu donne « non contrôlé » | Le taux de chariots en défaut ne doit ni cacher un défaut majeur, ni compter un chariot non contrôlé comme conforme |
| `stg_qualite__controles` | Libellé français jamais vide ; statuts connus ; chariot existant | Un nouveau code de défaut sans traduction | La source est en arabe : un code inconnu disparaîtrait des tableaux par défaut |
| Qualité | `assert_qualite_quantite_plausible` (avertissement) | Plus de 5 000 briques non acceptables pour un chariot | 20 saisies aberrantes (8 668 répété 14 fois) : à corriger dans l'application |
| `fct_controles_qualite`, `fct_chariots_qualite`, `fct_pesees_briques`, `agg_pertes_poids_jour`, `fct_mesures_briques` | **Contrats**, clés primaires ; zones, familles et statuts connus | Colonnes figées | Tables lues par l'API et Power BI |
| Rapprochement (`ingestion.rapprochement`) | Tables qui ne reçoivent que des ajouts (mesures) : source et entrepôt comparés **jusqu'à la dernière ligne copiée** (par identifiant) ; doublons comparés **des deux côtés** ; montants arrondis à 4 décimales avant la somme | Une mesure arrivée après la copie, un doublon déjà dans la source ou l'addition d'un million de nombres décimaux ne sont plus pris pour des erreurs de copie | Sans ces trois précautions, le rapprochement des machines était toujours en écart |
| Sources | `dbt source freshness` | La copie `raw_x3` a moins de 4 h (avertissement), moins de 24 h (erreur) | Un chargement arrêté ne doit pas passer inaperçu : les chiffres seraient vieux sans le savoir |

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
| Entrepôt (dbt) | **Tests unitaires dbt dans la CI** | Les tests unitaires tournent aussi dans la CI, sur des tables raw vides créées pour l'occasion | Aujourd'hui ils tournent à chaque `dbt build` sur le poste |
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
