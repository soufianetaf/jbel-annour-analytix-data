"""Connexion aux sources SQL Server, toujours en lecture seule et sans bloquer.

Trois protections se superposent :

1. **Le compte** : un compte SQL Server qui n'a que le droit de lire
   (db_datareader). C'est la seule vraie garantie, appliquée par le serveur.
   ``verifier_droits`` contrôle que le compte utilisé n'a pas plus.
2. **La connexion** : ouverte en mode lecture seule, et identifiée par
   un nom d'application, pour que l'équipe informatique reconnaisse nos
   sessions sur le serveur.
3. **La session** : READ UNCOMMITTED (aucun verrou posé sur les tables
   lues) et un délai d'attente de verrou court, pour ne jamais ralentir
   Sage X3 ni les automates de l'usine.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Literal

from ingestion.config import Parametres, SourceSqlServer

if TYPE_CHECKING:
    import pyodbc

NOM_APPLICATION = "Jbel Annour Analytix"
DELAI_CONNEXION_S = 15
DELAI_VERROU_MS = 2000

# Caractères qui obligent à entourer une valeur d'accolades dans une
# chaîne de connexion ODBC (sinon un « ; » dans un mot de passe la casse).
_CARACTERES_SPECIAUX = set(";{}=")


def _valeur_odbc(valeur: str) -> str:
    """Protège une valeur de chaîne de connexion ODBC."""
    if _CARACTERES_SPECIAUX & set(valeur) or valeur != valeur.strip():
        return "{" + valeur.replace("}", "}}") + "}"
    return valeur


def chaine_connexion(
    source: SourceSqlServer,
    parametres: Parametres,
    database: str | None = None,
) -> str:
    """Construit la chaîne de connexion ODBC d'une source.

    ``database`` remplace la base par défaut de la source (utile pour le
    serveur de l'usine, qui héberge une quarantaine de bases).
    """
    if not source.host:
        raise ValueError("source non configurée : adresse du serveur absente")

    serveur = source.host if source.port is None else f"{source.host},{source.port}"
    elements: dict[str, str] = {
        "DRIVER": "{" + parametres.odbc_driver + "}",
        "SERVER": _valeur_odbc(serveur),
        "Encrypt": "yes",
        "TrustServerCertificate": "yes" if parametres.sqlserver_trust_cert else "no",
        "ApplicationIntent": "ReadOnly",
        "APP": _valeur_odbc(NOM_APPLICATION),
    }

    base = database or source.database
    if base:
        elements["DATABASE"] = _valeur_odbc(base)

    if source.auth == "windows":
        elements["Trusted_Connection"] = "yes"
    else:
        assert source.user and source.password  # garanti par la configuration
        elements["UID"] = _valeur_odbc(source.user)
        elements["PWD"] = _valeur_odbc(source.password.get_secret_value())

    return ";".join(f"{cle}={valeur}" for cle, valeur in elements.items())


def ouvrir_connexion(
    source: SourceSqlServer,
    parametres: Parametres,
    database: str | None = None,
    read_uncommitted: bool = True,
) -> pyodbc.Connection:
    """Ouvre une connexion en lecture seule, sans verrou (à refermer soi-même).

    ``read_uncommitted=False`` garde le niveau par défaut de SQL Server :
    réservé à dlt, dont la lecture du catalogue (option READPAST) est
    refusée en READ UNCOMMITTED. Ses lectures de données reçoivent alors
    l'option WITH (NOLOCK), qui a le même effet table par table.
    """
    import pyodbc  # importé ici : les tests sans pilote ODBC n'en ont pas besoin

    connexion = pyodbc.connect(
        chaine_connexion(source, parametres, database),
        readonly=True,
        autocommit=True,
        timeout=DELAI_CONNEXION_S,
    )
    curseur = connexion.cursor()
    # Niveau toujours fixé explicitement : le pilote ODBC réutilise les
    # connexions (pool), et une connexion recyclée peut garder le niveau de
    # sa session précédente (constaté sur le serveur de l'usine).
    if read_uncommitted:
        curseur.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
    else:
        curseur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
    curseur.execute(f"SET LOCK_TIMEOUT {DELAI_VERROU_MS}")
    curseur.close()
    return connexion


@contextmanager
def connecter(
    source: SourceSqlServer,
    parametres: Parametres,
    database: str | None = None,
) -> Iterator[pyodbc.Connection]:
    """Ouvre une connexion en lecture seule, sans verrou, puis la referme."""
    connexion = ouvrir_connexion(source, parametres, database)
    try:
        yield connexion
    finally:
        connexion.close()


def moteur_sqlalchemy(
    source: SourceSqlServer,
    parametres: Parametres,
    database: str | None = None,
):
    """Moteur SQLAlchemy pour dlt, dont chaque connexion passe par ``ouvrir_connexion``.

    dlt ne reçoit donc jamais une connexion ordinaire : toutes ses lectures
    sont faites en lecture seule, sous le nom « Jbel Annour Analytix »,
    avec un délai de verrou de 2 s. Les requêtes de données doivent passer
    par ``sans_verrou`` (option WITH (NOLOCK)). Aucun « pool » : la
    connexion est refermée après usage.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool

    return create_engine(
        "mssql+pyodbc://",
        creator=lambda: ouvrir_connexion(source, parametres, database, read_uncommitted=False),
        poolclass=NullPool,
    )


def sans_verrou(requete, table):
    """Ajoute WITH (NOLOCK) à une requête SQLAlchemy de lecture d'une table.

    Utilisé par dlt (``query_adapter_callback``) : la lecture des données ne
    pose aucun verrou et n'attend aucun verrou, comme en READ UNCOMMITTED.
    """
    return requete.with_hint(table, "WITH (NOLOCK)", dialect_name="mssql")


# Requête de contrôle des droits du compte connecté. Elle ne lit que des
# fonctions système : aucune table, aucune donnée.
REQUETE_DROITS = """
SELECT
    SUSER_SNAME()                                      AS compte,
    DB_NAME()                                          AS base,
    IS_SRVROLEMEMBER('sysadmin')                       AS sysadmin,
    HAS_PERMS_BY_NAME(NULL, NULL, 'CONTROL SERVER')    AS control_server,
    IS_ROLEMEMBER('db_owner')                          AS db_owner,
    IS_ROLEMEMBER('db_datawriter')                     AS db_datawriter,
    IS_ROLEMEMBER('db_ddladmin')                       AS db_ddladmin,
    HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'INSERT') AS peut_inserer,
    HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'UPDATE') AS peut_modifier,
    HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'DELETE') AS peut_supprimer,
    HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'ALTER')  AS peut_alterer
"""

# Droit trouvé → explication lisible
_DROITS_INTERDITS = {
    "sysadmin": "administrateur de tout le serveur (sysadmin, comme le compte « sa »)",
    "control_server": "contrôle total du serveur (CONTROL SERVER)",
    "db_owner": "propriétaire de la base (db_owner)",
    "db_datawriter": "écriture dans toutes les tables (db_datawriter)",
    "db_ddladmin": "modification de la structure des tables (db_ddladmin)",
    "peut_inserer": "droit INSERT sur la base",
    "peut_modifier": "droit UPDATE sur la base",
    "peut_supprimer": "droit DELETE sur la base",
    "peut_alterer": "droit ALTER sur la base",
}


# Droits d'écriture vérifiés sur un schéma (ex. le dossier X3 BASE1)
DROITS_SCHEMA = ("INSERT", "UPDATE", "DELETE", "ALTER", "CONTROL")


def droits_interdits(droits: dict[str, Any]) -> list[str]:
    """Liste les droits d'écriture ou d'administration du compte.

    Une liste vide signifie que le compte est bien en lecture seule,
    au niveau du serveur, de la base et des schémas vérifiés. Les droits
    accordés table par table ne sont pas couverts : c'est à l'équipe
    informatique de ne donner que db_datareader.
    """
    problemes = [
        explication for cle, explication in _DROITS_INTERDITS.items() if droits.get(cle) == 1
    ]
    for schema, droits_schema in droits.get("schemas", {}).items():
        problemes.extend(
            f"droit {droit} sur le schéma {schema}"
            for droit in DROITS_SCHEMA
            if droits_schema.get(droit) == 1
        )
    return problemes


Decision = Literal["ok", "tolere", "refuse"]


def decision_compte(problemes: list[str], compte_admin_accepte: bool) -> Decision:
    """Décide si l'on peut lire une source avec ce compte.

    - ``ok``     : compte en lecture seule ;
    - ``tolere`` : compte qui peut écrire, accepté explicitement dans .env
      (dérogation décidée par l'entreprise, en dev comme en prod) ;
    - ``refuse`` : compte qui peut écrire, sans dérogation.

    Avec un compte toléré, la lecture seule n'est plus garantie par le
    serveur : seul le code d'Analytix, qui n'exécute que des lectures,
    protège la source.
    """
    if not problemes:
        return "ok"
    if compte_admin_accepte:
        return "tolere"
    return "refuse"


def verifier_droits(
    connexion: pyodbc.Connection,
    schemas: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Interroge le serveur sur les droits du compte connecté.

    ``schemas`` : schémas dont on vérifie aussi les droits d'écriture.
    Pour Sage X3, c'est le dossier (BASE1), où un compte peut avoir reçu
    des droits sans être membre d'aucun rôle.
    """
    curseur = connexion.cursor()
    curseur.execute(REQUETE_DROITS)
    ligne = curseur.fetchone()
    colonnes = [description[0] for description in curseur.description]
    droits: dict[str, Any] = dict(zip(colonnes, ligne, strict=True))

    droits["schemas"] = {}
    for schema in schemas:
        droits["schemas"][schema] = {
            droit: curseur.execute(
                "SELECT HAS_PERMS_BY_NAME(?, 'SCHEMA', ?)", schema, droit
            ).fetchval()
            for droit in DROITS_SCHEMA
        }
    curseur.close()
    return droits
