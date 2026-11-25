"""Vérifie que les macros de nettoyage de staging sont appliquées aux bons types.

Les macros texte_x3, date_x3 et horodatage_x3 ne s'appliquent qu'à un
texte ou à une date. Dans Sage X3, une même colonne peut être un texte
dans une table et un nombre dans une autre (SAC_0, UPDCOD_0, FIY_0…) :
l'erreur n'apparaît qu'à la construction dbt, une colonne à la fois.

Ce script lit les vrais types dans l'entrepôt (couche raw) et liste
d'un coup toutes les incohérences. À lancer après une première copie,
avant d'écrire ou de modifier un modèle staging :

    uv run python -m infra.ci.verifier_types_staging

Lecture seule ; code de sortie 1 s'il y a une incohérence.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOSSIER_STAGING = Path(__file__).resolve().parents[2] / "dbt" / "models" / "staging"

TYPES_ATTENDUS = {
    "texte_x3": {"character varying", "text"},
    "date_x3": {"timestamp without time zone", "date"},
    "horodatage_x3": {"timestamp without time zone"},
}
MOTIF_SOURCE = re.compile(r"source\('(\w+)', '(\w+)'\)")
MOTIF_MACRO = re.compile(r"(texte_x3|date_x3|horodatage_x3)\('(\w+)'\)")


def incoherences(types: dict[tuple[str, str, str], str]) -> list[str]:
    """Liste « fichier : macro(colonne) mais la colonne est de type … »."""
    problemes = []
    for fichier in sorted(DOSSIER_STAGING.rglob("stg_*.sql")):
        sql = fichier.read_text(encoding="utf-8")
        trouve = MOTIF_SOURCE.search(sql)
        if not trouve:
            continue
        schema, table = f"raw_{trouve.group(1)}", trouve.group(2)
        for macro, colonne in MOTIF_MACRO.findall(sql):
            reel = types.get((schema, table, colonne))
            if reel is None:
                problemes.append(f"{fichier.name} : {colonne} absente de {schema}.{table}")
            elif reel not in TYPES_ATTENDUS[macro]:
                problemes.append(f"{fichier.name} : {macro}({colonne}) mais la colonne est {reel}")
    return problemes


def main() -> int:
    import psycopg2

    from ingestion.config import EntrepotChargeur

    entrepot = EntrepotChargeur()
    connexion = psycopg2.connect(
        host=entrepot.host,
        port=entrepot.port,
        dbname=entrepot.database,
        user=entrepot.user,
        password=entrepot.password.get_secret_value(),
    )
    connexion.set_session(readonly=True)
    with connexion, connexion.cursor() as curseur:
        curseur.execute(
            "SELECT table_schema, table_name, column_name, data_type "
            "FROM information_schema.columns WHERE table_schema LIKE 'raw\\_%'"
        )
        types = {(s, t, c): d for s, t, c, d in curseur.fetchall()}
    connexion.close()

    problemes = incoherences(types)
    for probleme in problemes:
        print(f"  - {probleme}")
    print("OK : types cohérents." if not problemes else f"{len(problemes)} incohérence(s).")
    return 1 if problemes else 0


if __name__ == "__main__":
    sys.exit(main())
