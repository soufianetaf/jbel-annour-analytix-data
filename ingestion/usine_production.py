"""Copie de la production (serveur de l'usine, base production_2026) vers l'entrepôt.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.usine_production --simulation
    uv run python -m ingestion.usine_production

    production_2026.production.finposts             fiches de fin de poste
    production_2026.production.productionposts      réalisé et objectif par zone et poste
    production_2026.production.objectifzones        zones et objectifs
    production_2026.production.raisons              raisons d'écart
    production_2026.production.productionpost_raison  raisons par ligne de production
    production_2026.production.consomations         consommations journalières (énergie)
    production_2026.production.poidsbriques         contrôles de poids (qualité)
    production_2026.production.poidsbriques_infos   pesées

Seule production_2026 est lue : elle contient déjà l'historique de
l'ancienne base « production » (vérifié le 25/11/2026), lire les deux
compterait ces postes deux fois.

Jamais copiés : les fiches de début de poste (nom du chef d'équipe), la
table des sessions web (adresses IP), les identifiants des utilisateurs
et les commentaires en texte libre.
"""

from __future__ import annotations

import argparse
import sys

from ingestion.x3 import Cible, TableX3, charger

PRODUCTION = Cible(
    source="usine", base="production_2026", schema_source="production", schema_raw="raw_production"
)

TABLES = (
    TableX3(
        nom="finposts",
        cle=("id",),
        seulement=(
            "id",
            "selected_date",  # date du poste
            "shift",  # 07h00 - 15h00, 15h00 - 23h00, 23h00 - 07h00
            "equipe",  # A, B, C, D
            "status",
            "production_poste",
            "realise_post_budget",
            "nombre_palette",
            "nombreEtageres",
            "paletteEmpileuse",
            "en_cours_wagon",
            "created_at",
            "updated_at",
            "deleted_at",
        ),
    ),
    TableX3(
        nom="productionposts",
        cle=("id",),
        montant="saisie",  # réalisé
        seulement=(
            "id",
            "finpost_id",
            "objectifzone_id",
            "libelle",  # zone
            "saisie",  # réalisé
            "objectif",
            "created_at",
            "updated_at",
        ),
    ),
    TableX3(
        nom="objectifzones",
        cle=("id",),
        seulement=("id", "libelle", "objectif", "etat", "created_at", "updated_at"),
    ),
    TableX3(
        nom="raisons",
        cle=("id",),
        seulement=("id", "libelle", "objectifzone_id", "etat", "created_at", "deleted_at"),
    ),
    TableX3(
        nom="productionpost_raison",
        cle=("id",),
        seulement=("id", "productionpost_id", "raison_id", "raison", "created_at"),
    ),
    # Consommations journalières : saisies en texte dans l'application ;
    # converties en nombres dans staging (cahier des charges 5.2)
    TableX3(
        nom="consomations",
        cle=("id",),
        seulement=(
            "id",
            "date",
            "heure_rapport",
            "etat",
            "Fuel_stock",
            "Coke_stock",
            "coke_arrivages",
            "Fuel_arrivages",
            "Consommation_Électrique",
            "Consommation_Fuel_Four",
            "Consommation_Charbon",
            "Consommation_Coke_Four",
            "Consommation_Coke_Micronésie",
            "Consommation_Faitour",
            "Consommation_Propane",
            "Consommation_Propane_Kg",
            "prod_four",
            "Vitesse_de_Four",
            "type_de_briques",
            "nombre_de_wagon",
            "Pois_du_Briques_en_kg",
            "quantite_de_Briques",
            "Total_Production_en_Tonne",
            "consomationelectriquetotal",
            "fuelfourprecedant",
            "fuelfouractuel",
            "fuelsechoirprecedant",
            "fuelsechoiractuel",
            "silo1actuel",
            "silo1precedant",
            "silo2actuel",
            "silo2precedant",
            "created_at",
            "updated_at",
            "deleted_at",
        ),
    ),
    TableX3(
        nom="poidsbriques",
        cle=("id",),
        seulement=("id", "date", "heure", "shift", "etat", "created_at", "deleted_at"),
    ),
    TableX3(
        nom="poidsbriques_infos",
        cle=("id",),
        seulement=(
            "id",
            "poidsbrique_id",
            "zone",
            "type",
            "poids1",
            "poids2",
            "poids3",
            "poids4",
            "poids5",
            "poids6",
            "poids7",
            "poids8",
            "totalWeight",
            "created_at",
        ),
    ),
)


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    options = parseur.parse_args(arguments)
    charger("usine_production", TABLES, simulation=options.simulation, cible=PRODUCTION)
    if options.simulation:
        return 0

    from ingestion.rapprochement import rapprocher_tables

    return 0 if rapprocher_tables(TABLES, PRODUCTION) else 1


if __name__ == "__main__":
    sys.exit(main())
