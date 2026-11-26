"""Copie des contrôles qualité (serveur de l'usine, base qualite) vers l'entrepôt.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.usine_qualite --simulation
    uv run python -m ingestion.usine_qualite

    qualite.qualite.rapport_infos        en-têtes de contrôle (date, poste)
    qualite.qualite.rapports             rapports de contrôle
    qualite.qualite.rapport_composantes  chariots contrôlés en sortie du four
    qualite.qualite.controles            défauts contrôlés par chariot (liste fixe)
    qualite.qualite.infos                prélèvements de mesure (zone, type de brique)
    qualite.qualite.groups               mesures de briques (poids, dimensions)

Les pesées de l'application de production (poidsbriques) sont déjà copiées
par ingestion.usine_production.

Jamais copiés : le nom du freineur, l'identifiant de l'utilisateur, les
observations, emplacements, corrections et notes en texte libre, les photos.
Pas copiés non plus : les bases qualite_check (essais d'une journée, août
2025) et qualite_prod (application pilote, deux semaines d'octobre 2026),
ni les dosages (juin 2025, libellés d'essai).
"""

from __future__ import annotations

import argparse
import sys

from ingestion.x3 import Cible, TableX3, charger

QUALITE = Cible(source="usine", base="qualite", schema_source="qualite", schema_raw="raw_qualite")

TABLES = (
    TableX3(
        nom="rapport_infos",
        cle=("id",),
        seulement=("id", "date_controle", "shift", "created_at", "updated_at"),
    ),
    TableX3(
        nom="rapports",
        cle=("id",),
        seulement=(
            "id",
            "rapport_info_id",
            "status",
            "list",  # numéro de la liste de contrôle
            "date",
            "time",
            "shift",
            "created_at",
            "updated_at",
        ),
    ),
    TableX3(
        nom="rapport_composantes",
        cle=("id",),
        seulement=(
            "id",
            "rapport_id",
            "type_brique",
            "temps_sortie_four",
            "numero_chariot",
            "controle_time",
            "created_at",
            "updated_at",
        ),
    ),
    TableX3(
        nom="controles",
        cle=("id",),
        montant="quantite_non_acceptable",
        seulement=(
            "id",
            "composante_id",
            "code",  # code du défaut
            "libelle",  # libellé du défaut (en arabe)
            "status",  # green, yellow, red, blue
            "origine",
            "quantite_endomagé",  # orthographe de la source
            "defect_acceptable",
            "quantite_non_acceptable",
            "is_separable",
            "created_at",
            "updated_at",
        ),
    ),
    TableX3(
        nom="infos",
        cle=("id",),
        seulement=("id", "rapport_id", "zone", "type", "referance", "created_at"),
    ),
    TableX3(
        nom="groups",
        cle=("id",),
        montant="poids",
        seulement=("id", "info_id", "poids", "haut", "large", "long", "created_at"),
    ),
)


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    options = parseur.parse_args(arguments)
    charger("usine_qualite", TABLES, simulation=options.simulation, cible=QUALITE)
    if options.simulation:
        return 0

    from ingestion.rapprochement import rapprocher_tables

    return 0 if rapprocher_tables(TABLES, QUALITE) else 1


if __name__ == "__main__":
    sys.exit(main())
