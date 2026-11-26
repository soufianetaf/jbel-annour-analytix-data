# API de Jbel Annour Analytix

L'interface web (dépôt séparé) et les autres clients ne lisent **jamais** l'entrepôt directement : ils passent par cette API, qui applique les rôles côté serveur et journalise chaque accès. Le contrat entre les deux dépôts est le schéma **OpenAPI** publié par l'API.

## Lancer l'API en développement

```powershell
uv run uvicorn api.main:app --reload
```

- Documentation interactive : http://localhost:8000/docs
- Schéma OpenAPI (pour l'interface React) : http://localhost:8000/openapi.json
- Variables du `.env` : `DW_HOST`, `DW_PORT`, `DW_DATABASE`, `API_DB_USER`, `API_DB_PASSWORD`, `API_SECRET_KEY` (32 caractères aléatoires au moins), `API_DUREE_JETON_MINUTES`, `API_CORS_ORIGINS`.

## Créer les comptes

Les comptes sont dans la table `api.utilisateurs` de l'entrepôt (créée par `infra.postgres.initialiser_entrepot`). Le mot de passe est demandé au clavier, deux fois, 12 caractères au moins ; seule son **empreinte Argon2** est écrite, jamais le mot de passe.

```powershell
uv run python -m api.comptes creer s.alami --role direction
```

```powershell
uv run python -m api.comptes creer r.bennani --role representant --representant R012
```

```powershell
uv run python -m api.comptes lister
```

Autres actions : `mot-de-passe IDENTIFIANT`, `desactiver IDENTIFIANT`, `activer IDENTIFIANT`. Un compte désactivé perd ses droits **à la requête suivante**, sans attendre la fin de son jeton.

## Se connecter

1. `POST /v1/auth/jeton` (formulaire `username`, `password`) → un jeton, valable 8 heures.
2. Chaque requête porte l'en-tête `Authorization: Bearer <jeton>`.
3. `GET /v1/auth/moi` : mon identifiant, mon rôle, les domaines auxquels j'ai droit.

Même réponse (« Identifiant ou mot de passe incorrect ») si l'identifiant n'existe pas, si le mot de passe est faux ou si le compte est désactivé : on ne devine pas quels comptes existent.

## Droits par rôle

La **seule** table des droits est `api/roles.py`. Chaque route déclare son domaine ; un rôle absent du domaine reçoit 403. Un test vérifie toute la matrice, rôle par rôle et route par route.

| Domaine | Rôles | Routes |
|---|---|---|
| ventes | direction, commercial, finance, représentant (**ses ventes seulement**) | `/v1/ventes/ca-mensuel`, `/v1/ventes/clients`, `/v1/ventes/cycle-mois`, `/v1/ventes/livre-non-facture` |
| finance | direction, finance | `/v1/finance/compte-de-resultat`, `/v1/finance/creances`, `/v1/finance/tresorerie` |
| achats | direction, achats, finance | `/v1/achats/mois`, `/v1/achats/fournisseurs`, `/v1/stock/sites`, `/v1/stock/articles`, `/v1/stock/equilibre-briques` |
| production | direction, production, maintenance | `/v1/production/postes`, `/v1/machines/jour`, `/v1/machines/performance`, `/v1/energie/jour`, `/v1/energie/prix`, `/v1/qualite/chariots`, `/v1/qualite/pertes-poids` |
| maintenance | direction, maintenance, production | `/v1/maintenance/zones`, `/v1/maintenance/interventions`, `/v1/maintenance/fiabilite` |
| cout_revient | direction, finance | `/v1/cout-revient/mois`, `/v1/cout-revient/marges` |
| direction | direction, finance | `/v1/direction/mois` |
| rh | direction, rh | `/v1/rh/effectifs`, `/v1/rh/presence` |
| qualite_donnees | tous, administrateur compris (comptages seulement) | `/v1/qualite-donnees` |

Chaque route lit une table de synthèse de `marts`, déjà rapprochée de sa source ; les définitions sont dans `docs/indicateurs/`. Les listes ont une limite (`limite`, 200 ou 500 au plus).

- **Représentant** : le filtre sur son code Sage X3 est dans la requête SQL, pas dans l'écran. Un compte représentant sans code ne voit rien.
- **Administrateur** : gère les comptes, ne voit aucune donnée métier.
- **Ajouter une route** : la déclarer dans un module de `api/routes/` avec `exiger_domaine("…")`, et ajouter le module à `ROUTEURS` dans `api/main.py`. Les tests la retrouvent seuls et vérifient ses droits pour chaque rôle.

Paramètres de période : `debut` et `fin` (AAAA-MM-JJ, inclus), un an par défaut, dix ans au plus.

## Sécurité

| Protection | Où |
|---|---|
| L'API ne peut rien écrire dans l'entrepôt : compte `analytix_api` sans droit d'écriture, lecture seule forcée par le serveur et redemandée à chaque connexion | `infra/postgres/initialiser_entrepot.py`, `api/base.py` |
| L'API ne lit que `marts` et `api.utilisateurs` ; jamais `staging`, `raw_*`, ni le détail des erreurs de données | droits PostgreSQL, tests `-m entrepot` |
| Requêtes SQL avec paramètres, jamais de texte de l'utilisateur collé dans le SQL | `api/routes/*` |
| Requête interrompue au-delà de 30 secondes | rôle `analytix_api` |
| Jetons signés (HS256) par `API_SECRET_KEY`, expiration, compte relu à chaque requête | `api/securite.py` |
| CORS limité à l'adresse de l'interface | `API_CORS_ORIGINS` |

## Journal des accès

Une ligne JSON par requête (journal `analytix.acces`, sur la sortie de l'API) : date, utilisateur, rôle, méthode, chemin, filtres, statut, durée, adresse du client. Jamais de mot de passe ni de jeton.

```json
{"le": "2026-11-26T10:12:03+00:00", "utilisateur": "s.alami", "role": "direction", "methode": "GET", "chemin": "/v1/direction/mois", "filtres": {"debut": "2026-01-01"}, "statut": 200, "duree_ms": 41.2, "client": "<adresse du poste>"}
```

## À venir

1. Les routes que l'interface demandera (détail par client, par article, par machine…), au fil de son développement.
2. Connexion par l'annuaire de l'entreprise (Active Directory) quand il sera disponible : seule la vérification du mot de passe changera.
3. Limiter les tentatives de connexion (par adresse et par compte).
4. Sécurité par ligne dans PostgreSQL (cahier des charges), pour que Power BI applique les mêmes règles que l'API.
