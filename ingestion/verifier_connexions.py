"""Vérifie la connexion à chaque source et que son compte est en lecture seule.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.verifier_connexions

Pour chaque source renseignée dans .env : connexion, compte utilisé,
version du serveur, puis contrôle des droits. Aucune table n'est lue.

Code de sortie : 0 si toutes les sources configurées répondent avec un
compte en lecture seule, 1 sinon.
"""

from __future__ import annotations

import sys

from ingestion.config import SourceX3, parametres, sources
from ingestion.sqlserver import connecter, droits_interdits, verifier_droits


def main() -> int:
    params = parametres()
    tout_va_bien = True
    print(f"Environnement : {params.analytix_env}\n")

    for nom, source in sources().items():
        if not source.configuree:
            print(f"[{nom}] non configurée dans .env : ignorée\n")
            continue

        print(f"[{nom}] connexion…")
        try:
            with connecter(source, params) as connexion:
                version = connexion.getinfo(18)  # SQL_DBMS_VER : version du serveur
                # Pour Sage X3, on vérifie aussi le schéma du dossier (BASE1)
                schemas = (source.dossier,) if isinstance(source, SourceX3) else ()
                droits = verifier_droits(connexion, schemas)
        except Exception as erreur:  # on continue : chaque source est testée
            # Le message du pilote ne contient jamais le mot de passe.
            print(f"  ÉCHEC de la connexion : {type(erreur).__name__}: {erreur}\n")
            tout_va_bien = False
            continue

        print(f"  compte  : {droits['compte']}")
        print(f"  base    : {droits['base']}")
        print(f"  version : SQL Server {version}")

        problemes = droits_interdits(droits)
        if problemes:
            tout_va_bien = False
            print("  DROITS : REFUSÉ, ce compte peut modifier la source :")
            for probleme in problemes:
                print(f"    - {probleme}")
            print("  → Demander à l'informatique un compte limité à db_datareader.\n")
        else:
            print("  droits  : OK, lecture seule\n")

    if not any(source.configuree for source in sources().values()):
        print("Aucune source configurée : remplir .env à partir de .env.example.")
        tout_va_bien = False

    print("Résultat : OK" if tout_va_bien else "Résultat : À CORRIGER")
    return 0 if tout_va_bien else 1


if __name__ == "__main__":
    sys.exit(main())
