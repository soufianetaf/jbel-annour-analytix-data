"""Gestion des comptes de la plateforme (table api.utilisateurs).

Utilisation, depuis la racine du dépôt :

    uv run python -m api.comptes lister
    uv run python -m api.comptes creer s.alami --role direction
    uv run python -m api.comptes creer r.bennani --role representant --representant R012
    uv run python -m api.comptes mot-de-passe s.alami
    uv run python -m api.comptes desactiver s.alami

Le mot de passe est demandé au clavier (jamais en argument : il resterait
dans l'historique du terminal), deux fois, 12 caractères au moins. Seule son
empreinte Argon2 est écrite. L'outil se connecte avec le compte du chargeur
(DW_USER), le seul qui peut écrire dans le schéma api ; l'API, elle, ne
fait que lire.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from api.roles import ROLES
from api.securite import empreinte

LONGUEUR_MIN_MOT_DE_PASSE = 12


def demander_mot_de_passe() -> str:
    premier = getpass.getpass("Mot de passe : ")
    if len(premier) < LONGUEUR_MIN_MOT_DE_PASSE:
        raise SystemExit(
            f"Mot de passe trop court : {LONGUEUR_MIN_MOT_DE_PASSE} caractères au moins"
        )
    if getpass.getpass("Encore une fois : ") != premier:
        raise SystemExit("Les deux mots de passe sont différents")
    return premier


def _connexion():
    import psycopg

    from ingestion.config import EntrepotChargeur

    chargeur = EntrepotChargeur()
    return psycopg.connect(
        host=chargeur.host,
        port=chargeur.port,
        dbname=chargeur.database,
        user=chargeur.user,
        password=chargeur.password.get_secret_value(),
        application_name="Jbel Annour Analytix - comptes",
    )


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parseur.add_subparsers(dest="action", required=True)
    actions.add_parser("lister", help="comptes, rôles et état (jamais les empreintes)")
    creer = actions.add_parser("creer", help="nouveau compte")
    creer.add_argument("identifiant")
    creer.add_argument("--role", required=True, choices=ROLES)
    creer.add_argument("--representant", help="code représentant Sage X3 (rôle representant)")
    for action in ("mot-de-passe", "desactiver", "activer"):
        actions.add_parser(action).add_argument("identifiant")
    options = parseur.parse_args(arguments)

    if getattr(options, "role", None) == "representant" and not options.representant:
        raise SystemExit("Un compte representant doit avoir son code : --representant CODE")

    with _connexion() as connexion, connexion.cursor() as curseur:
        if options.action == "lister":
            curseur.execute(
                "SELECT identifiant, role, representant, actif, modifie_le "
                "FROM api.utilisateurs ORDER BY identifiant"
            )
            for ligne in curseur.fetchall():
                print(*ligne, sep="  |  ")
            return 0

        identifiant = options.identifiant.strip().lower()
        if options.action == "creer":
            curseur.execute(
                "INSERT INTO api.utilisateurs "
                "(identifiant, empreinte_mot_de_passe, role, representant) "
                "VALUES (%s, %s, %s, %s)",
                (
                    identifiant,
                    empreinte(demander_mot_de_passe()),
                    options.role,
                    options.representant,
                ),
            )
        elif options.action == "mot-de-passe":
            curseur.execute(
                "UPDATE api.utilisateurs SET empreinte_mot_de_passe = %s, modifie_le = now() "
                "WHERE identifiant = %s",
                (empreinte(demander_mot_de_passe()), identifiant),
            )
        else:
            curseur.execute(
                "UPDATE api.utilisateurs SET actif = %s, modifie_le = now() WHERE identifiant = %s",
                (options.action == "activer", identifiant),
            )
        if curseur.rowcount != 1:
            raise SystemExit(f"Compte « {identifiant} » introuvable")
    print(f"Compte « {identifiant} » : {options.action} fait.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
