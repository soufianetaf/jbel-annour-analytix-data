"""Copie des 13 compteurs électriques (serveur de l'usine, base electrique_data).

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.usine_electricite --simulation
    uv run python -m ingestion.usine_electricite
    uv run python -m ingestion.usine_electricite --complet   # recopie entière

Chaque compteur a sa table, toutes de même structure (tensions, courants,
cos φ, puissances, index d'énergie). Un relevé environ tous les quarts
d'heure ; un relevé ne change jamais une fois écrit : copie incrémentale
sur la date du relevé (reprise d'un jour), fusion par identifiant, et
rapprochement arrêté au dernier identifiant copié. Aucune donnée personnelle.
"""

from __future__ import annotations

import argparse
import sys

from ingestion.x3 import Cible, TableX3, charger

ELECTRICITE = Cible(
    source="usine", base="electrique_data", schema_source="dbo", schema_raw="raw_electrique_data"
)

# Compteurs généraux, puis compteurs par machine (en aval des premiers)
COMPTEURS = (
    "entree",
    "transfo1",
    "transfo2",
    "argile",
    "prepa1",
    "prepa2",
    "extrudeuse",
    "sechoir",
    "empileuse",
    "four",
    "depileuse",
    "compresseur",
    "eclirage",  # orthographe de la source : éclairage
)

_COLONNES = (
    "id",
    "date_insert",  # date et heure du relevé
    "Tansion_1",  # orthographe de la source : tension
    "Tansion_2",
    "Tansion_3",
    "Tansion_M",
    "courant_1",
    "courant_2",
    "courant_3",
    "courant_M",
    "cos_phi_1",
    "cos_phi_2",
    "cos_phi_3",
    "cos_phi_M",
    "P_Tot",  # puissance active totale
    "Q_Tot",  # puissance réactive totale
    "S_Tot",  # puissance apparente totale
    "cons_P_total",  # index d'énergie active cumulé
    "cons_P_total_j_1",  # consommation de la veille
    "cons_P_plein_j_1",  # veille, heures pleines
    "cons_P_pointe_j_1",  # veille, heures de pointe
    "cons_P_creuse_j_1",  # veille, heures creuses
)

TABLES = tuple(
    TableX3(
        nom=f"{compteur}_elect",
        cle=("id",),
        montant="P_Tot",
        incremental="date_insert",
        lag_jours=1,
        ajout_seul=True,
        seulement=_COLONNES,
    )
    for compteur in COMPTEURS
)


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    parseur.add_argument("--complet", action="store_true", help="recopie entière")
    options = parseur.parse_args(arguments)
    charger(
        "usine_electricite",
        TABLES,
        simulation=options.simulation,
        complet=options.complet,
        cible=ELECTRICITE,
    )
    if options.simulation:
        return 0

    from ingestion.rapprochement import rapprocher_tables

    return 0 if rapprocher_tables(TABLES, ELECTRICITE) else 1


if __name__ == "__main__":
    sys.exit(main())
