"""Crée ou met à niveau l'entrepôt PostgreSQL : rôles, base, schémas, droits.

Utilisation, depuis la racine du dépôt :

    # Afficher ce qui serait exécuté, sans rien exécuter
    uv run python -m infra.postgres.initialiser_entrepot --simulation

    # Exécuter
    uv run python -m infra.postgres.initialiser_entrepot

Le script se connecte avec le compte administrateur (DW_ADMIN_USER), car
lui seul peut créer des rôles et des bases. Ce compte ne sert qu'ici :
l'ingestion, dbt et l'API utilisent leurs propres comptes, aux droits
limités.

Il est **idempotent** : le relancer ne casse rien. Il crée ce qui manque
et remet les droits à l'état attendu.

Garde-fou : il ne touche qu'à une base nommée dw_dev, dw_prod ou dw_test.
Les autres bases du serveur (projets voisins, pilote dw_ventes) ne sont
jamais modifiées.

Ce que l'on obtient :

    analytix_chargeur       compte de l'ingestion et de dbt
                            propriétaire de la base et de tous les schémas
    analytix_lecture_marts  groupe (sans connexion) : lecture du schéma marts
    analytix_api            compte de l'API, membre du groupe ci-dessus,
                            en lecture seule forcée par le serveur

    base dw_dev
      staging, intermediate, marts, snapshots, quality
      (les schémas raw_<source> sont créés par l'ingestion)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

FICHIER_ENV = Path(__file__).resolve().parents[2] / ".env"

# Seules ces bases peuvent être créées ou modifiées par ce script.
BASES_AUTORISEES = re.compile(r"^dw_(dev|prod|test)$")
# Noms de rôles et de schémas : minuscules, chiffres, « _ » (aucune injection possible)
IDENTIFIANT = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")

PREFIXE_ROLES = "analytix_"
GROUPE_LECTURE_MARTS = "analytix_lecture_marts"
SCHEMAS = ("staging", "intermediate", "marts", "snapshots", "quality")
FUSEAU_HORAIRE = "Africa/Casablanca"
# Une requête de l'API plus longue que ce délai est interrompue
DELAI_REQUETE_API = "30s"


class ConfigEntrepot(BaseSettings):
    """Variables DW_… et API_DB_… du fichier .env."""

    model_config = SettingsConfigDict(
        env_file=FICHIER_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    dw_host: str = "localhost"
    dw_port: int = 5432
    dw_database: str = "dw_dev"
    dw_admin_user: str = "postgres"
    dw_admin_password: SecretStr | None = None
    dw_user: str = "analytix_chargeur"
    dw_password: SecretStr
    api_db_user: str = "analytix_api"
    api_db_password: SecretStr

    @field_validator("dw_database")
    @classmethod
    def _base_autorisee(cls, valeur: str) -> str:
        if not BASES_AUTORISEES.match(valeur):
            raise ValueError(
                f"base « {valeur} » refusée : seules dw_dev, dw_prod et dw_test sont gérées "
                "par ce script (les autres bases du serveur ne sont jamais touchées)"
            )
        return valeur

    @field_validator("dw_user", "api_db_user")
    @classmethod
    def _role_gere(cls, valeur: str) -> str:
        # Le script modifie les rôles qu'il gère (mot de passe, droits) : il
        # ne doit jamais toucher « postgres », « dw_ventes » ni le rôle d'un
        # autre projet. Seuls les rôles analytix_… sont acceptés.
        if not (IDENTIFIANT.match(valeur) and valeur.startswith(PREFIXE_ROLES)):
            raise ValueError(
                f"rôle « {valeur} » refusé : le nom doit commencer par « {PREFIXE_ROLES} » "
                "(minuscules, chiffres, _)"
            )
        return valeur


@dataclass
class Instruction:
    """Une instruction SQL, avec ses paramètres (ex. un mot de passe)."""

    sql: str
    parametres: tuple[str, ...] = ()
    # Paramètres secrets : remplacés par ******** à l'affichage
    secret: bool = False

    def affichage(self) -> str:
        if not self.parametres:
            return self.sql
        valeurs = ["'********'" if self.secret else f"'{p}'" for p in self.parametres]
        return self.sql.replace("%s", "{}").format(*valeurs)


@dataclass
class Plan:
    """Tout ce que le script exécute, dans l'ordre."""

    # Exécutées sur la base « postgres » : rôles et base
    serveur: list[Instruction] = field(default_factory=list)
    # Exécutées dans l'entrepôt, en une seule transaction
    entrepot: list[Instruction] = field(default_factory=list)


def _q(identifiant: str) -> str:
    """Identifiant SQL entre guillemets (déjà validé par IDENTIFIANT)."""
    assert IDENTIFIANT.match(identifiant), identifiant
    return f'"{identifiant}"'


def plan_roles(config: ConfigEntrepot, roles_existants: set[str]) -> list[Instruction]:
    """Création des rôles, ou mise à jour de leur mot de passe."""
    instructions: list[Instruction] = []
    roles = [
        (config.dw_user, config.dw_password, "LOGIN"),
        (config.api_db_user, config.api_db_password, "LOGIN"),
    ]
    for role, mot_de_passe, option in roles:
        verbe = "ALTER" if role in roles_existants else "CREATE"
        instructions.append(
            Instruction(
                f"{verbe} ROLE {_q(role)} WITH {option} NOSUPERUSER NOCREATEDB "
                "NOCREATEROLE NOREPLICATION PASSWORD %s",
                (mot_de_passe.get_secret_value(),),
                secret=True,
            )
        )
    if GROUPE_LECTURE_MARTS not in roles_existants:
        instructions.append(Instruction(f"CREATE ROLE {_q(GROUPE_LECTURE_MARTS)} NOLOGIN"))

    api = _q(config.api_db_user)
    instructions += [
        Instruction(f"GRANT {_q(GROUPE_LECTURE_MARTS)} TO {api}"),
        # L'API ne peut écrire nulle part, même par erreur : le serveur refuse
        Instruction(f"ALTER ROLE {api} SET default_transaction_read_only = on"),
        Instruction(f"ALTER ROLE {api} SET statement_timeout = '{DELAI_REQUETE_API}'"),
    ]
    return instructions


def plan_base(config: ConfigEntrepot, base_existe: bool) -> list[Instruction]:
    """Création de la base, ou remise de son propriétaire."""
    base, chargeur = _q(config.dw_database), _q(config.dw_user)
    if base_existe:
        creation = Instruction(f"ALTER DATABASE {base} OWNER TO {chargeur}")
    else:
        creation = Instruction(
            f"CREATE DATABASE {base} OWNER {chargeur} ENCODING 'UTF8' TEMPLATE template0"
        )
    return [
        creation,
        # Personne ne se connecte à l'entrepôt sans y avoir été autorisé
        Instruction(f"REVOKE ALL ON DATABASE {base} FROM PUBLIC"),
        Instruction(f"GRANT CONNECT, CREATE, TEMPORARY ON DATABASE {base} TO {chargeur}"),
        Instruction(f"GRANT CONNECT ON DATABASE {base} TO {_q(GROUPE_LECTURE_MARTS)}"),
        Instruction(f"ALTER DATABASE {base} SET timezone TO '{FUSEAU_HORAIRE}'"),
    ]


def plan_entrepot(config: ConfigEntrepot) -> list[Instruction]:
    """Schémas et droits, à l'intérieur de l'entrepôt."""
    chargeur, lecture = _q(config.dw_user), _q(GROUPE_LECTURE_MARTS)
    instructions = [
        # Le schéma « public » n'est utilisable par personne
        Instruction("REVOKE ALL ON SCHEMA public FROM PUBLIC"),
    ]
    for schema in SCHEMAS:
        instructions += [
            Instruction(f"CREATE SCHEMA IF NOT EXISTS {_q(schema)} AUTHORIZATION {chargeur}"),
            Instruction(f"ALTER SCHEMA {_q(schema)} OWNER TO {chargeur}"),
            Instruction(f"REVOKE ALL ON SCHEMA {_q(schema)} FROM PUBLIC"),
        ]
    instructions += [
        # Le groupe de lecture ne voit que marts, et seulement en lecture
        Instruction(f'GRANT USAGE ON SCHEMA "marts" TO {lecture}'),
        Instruction(f'GRANT SELECT ON ALL TABLES IN SCHEMA "marts" TO {lecture}'),
        # … y compris pour les tables que dbt créera plus tard
        Instruction(
            f'ALTER DEFAULT PRIVILEGES FOR ROLE {chargeur} IN SCHEMA "marts" '
            f"GRANT SELECT ON TABLES TO {lecture}"
        ),
    ]
    return instructions


def construire_plan(config: ConfigEntrepot, roles_existants: set[str], base_existe: bool) -> Plan:
    return Plan(
        serveur=plan_roles(config, roles_existants) + plan_base(config, base_existe),
        entrepot=plan_entrepot(config),
    )


def afficher(plan: Plan, config: ConfigEntrepot) -> None:
    print("-- Sur la base « postgres » (rôles et base)")
    for instruction in plan.serveur:
        print(f"{instruction.affichage()};")
    print(f"\n-- Dans « {config.dw_database} », en une seule transaction")
    for instruction in plan.entrepot:
        print(f"{instruction.affichage()};")


def executer(config: ConfigEntrepot, simulation: bool) -> None:
    import psycopg2  # importé ici : les tests du plan n'en ont pas besoin

    if config.dw_admin_password is None:
        raise SystemExit("DW_ADMIN_PASSWORD manquant dans .env (compte administrateur PostgreSQL)")

    def connexion(base: str):
        return psycopg2.connect(
            host=config.dw_host,
            port=config.dw_port,
            dbname=base,
            user=config.dw_admin_user,
            password=config.dw_admin_password.get_secret_value(),
            connect_timeout=10,
            application_name="Jbel Annour Analytix - initialisation",
        )

    # 1. Lire l'état actuel du serveur (lecture seule)
    serveur = connexion("postgres")
    serveur.autocommit = True  # CREATE DATABASE ne peut pas être dans une transaction
    with serveur.cursor() as curseur:
        curseur.execute("SELECT rolname FROM pg_roles")
        roles_existants = {ligne[0] for ligne in curseur.fetchall()}
        curseur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (config.dw_database,))
        base_existe = curseur.fetchone() is not None

    plan = construire_plan(config, roles_existants, base_existe)
    print(f"Serveur {config.dw_host}:{config.dw_port}, base {config.dw_database}")
    print(f"Base déjà présente : {'oui' if base_existe else 'non'}\n")
    afficher(plan, config)

    if simulation:
        print("\nSimulation : rien n'a été exécuté.")
        serveur.close()
        return

    # 2. Rôles et base
    with serveur.cursor() as curseur:
        for instruction in plan.serveur:
            curseur.execute(instruction.sql, instruction.parametres or None)
    serveur.close()

    # 3. Schémas et droits, en une transaction : tout ou rien
    entrepot = connexion(config.dw_database)
    try:
        with entrepot, entrepot.cursor() as curseur:
            for instruction in plan.entrepot:
                curseur.execute(instruction.sql)
    finally:
        entrepot.close()

    print(f"\nTerminé : entrepôt « {config.dw_database} » prêt.")


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument(
        "--simulation", action="store_true", help="afficher le SQL sans l'exécuter"
    )
    options = parseur.parse_args(arguments)
    executer(ConfigEntrepot(), options.simulation)
    return 0


if __name__ == "__main__":
    sys.exit(main())
