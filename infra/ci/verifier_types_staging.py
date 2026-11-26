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
    "texte": {"character varying", "text"},
    "nombre_saisi": {"character varying", "text"},
    "date_seule": {"timestamp without time zone", "timestamp with time zone", "date"},
    "date_x3": {"timestamp without time zone", "date"},
    "horodatage_x3": {"timestamp without time zone"},
}
MOTIF_SOURCE = re.compile(r"source\('(\w+)', '(\w+)'\)")
MOTIF_MACRO = re.compile(
    r"(texte_x3|date_x3|horodatage_x3|nombre_saisi|texte|date_seule)\('(\w+)'\)"
)


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


def colonnes_absentes_de_raw(colonnes_raw: dict[tuple[str, str], set[str]]) -> list[str]:
    """Colonnes des listes fermées de l'ingestion qui n'existent pas dans raw.

    dlt ne crée pas une colonne dont toutes les valeurs sont vides : elle
    manque alors dans raw, et un modèle staging qui la cite échoue.
    """
    from dlt.common.normalizers.naming.snake_case import NamingConvention

    from ingestion import (
        usine_electricite,
        usine_machines,
        usine_magasin,
        usine_production,
        x3_achats,
        x3_finance,
        x3_stock,
        x3_ventes,
    )
    from ingestion.x3 import CIBLE_X3

    nommage = NamingConvention()
    groupes = [(m.TABLES, CIBLE_X3) for m in (x3_ventes, x3_finance, x3_stock, x3_achats)]
    groupes += [(tables, cible) for _, tables, cible in usine_magasin.COPIES]
    groupes += [(usine_production.TABLES, usine_production.PRODUCTION)]
    groupes += [(tables, cible) for _, tables, cible in usine_machines.COPIES]
    groupes += [(usine_electricite.TABLES, usine_electricite.ELECTRICITE)]
    absentes = []
    for tables, cible in groupes:
        for table in tables:
            if not table.seulement:
                continue
            reelles = colonnes_raw.get((cible.schema_raw, table.destination))
            if reelles is None:
                continue  # table pas encore copiée
            attendues = {nommage.normalize_identifier(c) for c in table.seulement}
            for colonne in sorted(attendues - reelles):
                absentes.append(f"{cible.schema_raw}.{table.destination}.{colonne}")
    return absentes


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

    colonnes_raw: dict[tuple[str, str], set[str]] = {}
    for schema, table, colonne in types:
        colonnes_raw.setdefault((schema, table), set()).add(colonne)
    for absente in colonnes_absentes_de_raw(colonnes_raw):
        # Information : la colonne est vide dans la source (dlt ne l'a pas créée)
        print(f"  info : {absente} absente de raw (vide dans la source ?)")

    problemes = incoherences(types)
    for probleme in problemes:
        print(f"  - {probleme}")
    print("OK : types cohérents." if not problemes else f"{len(problemes)} incohérence(s).")
    return 1 if problemes else 0


if __name__ == "__main__":
    sys.exit(main())
