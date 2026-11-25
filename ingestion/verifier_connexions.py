"""Vérifie la connexion à chaque source et que son compte est en lecture seule.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.verifier_connexions

Pour chaque source renseignée dans .env : connexion, compte utilisé,
version du serveur, puis contrôle des droits. Aucune table n'est lue.

Code de sortie : 0 si toutes les sources configurées répondent avec un
compte en lecture seule (ou un compte toléré par dérogation, voir
<SOURCE>_COMPTE_ADMIN_ACCEPTE dans .env.example), 1 sinon.
"""

from __future__ import annotations

import sys

from ingestion.config import SourceX3, parametres, sources
from ingestion.sqlserver import connecter, decision_compte, droits_interdits, verifier_droits


def main() -> int:
    params = parametres()
    tout_va_bien = True
    avertissements = 0
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
        decision = decision_compte(problemes, source.compte_admin_accepte)
        if decision == "ok":
            print("  droits  : OK, lecture seule\n")
            continue

        resume = ", ".join(problemes[:3]) + (" …" if len(problemes) > 3 else "")
        if decision == "tolere":
            avertissements += 1
            print("  droits  : ATTENTION, compte qui peut modifier la source")
            print(f"            ({resume})")
            print(f"            toléré par dérogation ({nom.upper()}_COMPTE_ADMIN_ACCEPTE=yes) ;")
            print("            Analytix n'exécute que des lectures sur cette source.\n")
        else:
            tout_va_bien = False
            print("  DROITS : REFUSÉ, ce compte peut modifier la source :")
            for probleme in problemes:
                print(f"    - {probleme}")
            print("  → Utiliser un compte limité à db_datareader, ou déclarer la dérogation")
            print(f"    dans .env : {nom.upper()}_COMPTE_ADMIN_ACCEPTE=yes\n")

    if not any(source.configuree for source in sources().values()):
        print("Aucune source configurée : remplir .env à partir de .env.example.")
        tout_va_bien = False

    if not tout_va_bien:
        print("Résultat : À CORRIGER")
    elif avertissements:
        print(f"Résultat : OK, avec {avertissements} compte(s) toléré(s) par dérogation")
    else:
        print("Résultat : OK")
    return 0 if tout_va_bien else 1


if __name__ == "__main__":
    sys.exit(main())
