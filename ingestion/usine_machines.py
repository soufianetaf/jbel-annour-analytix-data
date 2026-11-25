"""Copie des données des machines (serveur de l'usine) vers l'entrepôt.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.usine_machines --simulation
    uv run python -m ingestion.usine_machines
    uv run python -m ingestion.usine_machines --complet   # recopie entière des mesures

    moulage    : mesures du process (1,3 M lignes, incrémental), remplissage
                 des étagères, bilan journalier
    sechoir    : bilan journalier
    empileuse  : chargement des wagons, bilan journalier
    Four_prod  : bilan journalier, production par recette
    depileuse  : déchargement des wagons, temps de cycle, bilan journalier

Les mesures du moulage ne changent jamais une fois écrites : copie
incrémentale sur la date de la mesure (reprise d'un jour), fusion par
identifiant. Les autres tables sont petites : copie complète.

Jamais copié : le nom de l'opérateur (remplissage, chargement et
déchargement des wagons).
"""

from __future__ import annotations

import argparse
import sys

from ingestion.x3 import Cible, TableX3, charger


def _cible(base: str) -> Cible:
    return Cible(source="usine", base=base, schema_source="dbo", schema_raw=f"raw_{base.lower()}")


MOULAGE, SECHOIR, EMPILEUSE, FOUR, DEPILEUSE = (
    _cible("moulage"),
    _cible("sechoir"),
    _cible("empileuse"),
    _cible("Four_prod"),
    _cible("depileuse"),
)

TABLES_MOULAGE = (
    TableX3(
        nom="remplissage_process_data",
        cle=("Id",),
        montant="courant_extrudeuse",
        incremental="date_insert",
        lag_jours=1,
        ajout_seul=True,  # une mesure ne change jamais une fois écrite
        seulement=(
            "Id",
            "remplissage_id",
            "date_insert",  # date et heure de la mesure
            "vitesse_coupe",
            "vitesse_doseur",
            "pression_mono",
            "courant_extrudeuse",
        ),
    ),
    TableX3(
        nom="remplissage_etagere",
        cle=("Id",),
        seulement=(
            "Id",
            "debut_remplissage",
            "fin_remplissage",
            "ordre",
            "numero_etagere",
            "type_produit",
            "stock",
            "statut",
            "temps_remplissage",
        ),
    ),
    TableX3(
        nom="donnes_prod_mono",
        cle=("date_insert",),
        montant="nbr_chariot_reel",
        seulement=(
            "date_insert",
            "nbr_chariot_calcul",
            "nbr_chariot_reel",
            "Heure_marche",
            "heure_arret_total",
            "nbr_demarrage",
            "Heure_marche_vide",
            "nbr_debrayag",
            "vitesse_doseur",
            "vitesse_coupe",
            "pression_extrudeuse",
            "courant_extrudeuse",
        ),
    ),
)

TABLES_SECHOIR = (
    TableX3(
        nom="donnes_prod_sech",
        cle=("id",),
        montant="total_etageres",
        seulement=(
            "id",
            "date_insert",
            "total_etageres",
            "total_etageres_vide",
            "etat_generateur_1",
            "nbr_demarrage_genera_1",
            "heure_marche_genera_1",
            "heure_arret_genera_1",
            "etat_generateur_2",
            "nbr_demarrage_genera_2",
            "heure_marche_genera_2",
            "heure_arret_genera_2",
            "etat_generateur_3",
            "nbr_demarrage_genera_3",
            "heure_marche_genera_3",
            "heure_arret_genera_3",
        ),
    ),
)

TABLES_EMPILEUSE = (
    TableX3(
        nom="chargement_wagons",
        cle=("Id",),
        seulement=(
            "Id",
            "date_heure_entree",
            "date_heure_sortie",
            "ordre_wagon",
            "numero_reel_wagon",
            "temps_decharge",
        ),
    ),
    TableX3(
        nom="donnes_prod_emp",
        cle=("id",),
        montant="wagons_empiles",
        seulement=(
            "id",
            "date_insert",
            "etat_empileuse",
            "wagons_empiles",
            "etagere_decharge",
            "heure_marche_empileuse",
            "heure_arret_empileuse",
            "heure_marche_pinces",
            "heure_arret_pinces",
        ),
    ),
)

TABLES_FOUR = (
    TableX3(
        nom="donnes_prod_four",
        cle=("date_insert",),
        montant="qte_brique_tonne",
        seulement=(
            "date_insert",
            "recette",
            "type_produit",
            "poids_une_brique_kg",
            "qte_brique_produit_unit_wagon",
            "qte_brique_unite",
            "qte_brique_tonne",
            "ration_cuisson_cocke_kg_tonne",
            "consomm_coke_tonne",
            "cadence_consom_coke_tonne_hr",
            "qte_coke_livre_tonne",
            "cadence_prod_wagons",
            "nbr_pousse_faites",
            "nbr_brule_operationnel",
            "stock_coke_petrol_silo1",
            "stock_coke_petrol_silo2",
            "stock_fuel_reserv1",
            "heure_marche_vis1_coke",
            "heure_marche_vis2_coke",
            "cons_temp_chemine",
            "vr_temp_chemine",
            "cons_temp_voute",
            "vr_temp_voute",
            "cons_temp_fosse",
            "vr_temp_fosse",
        ),
    ),
    TableX3(
        nom="Production_four",
        cle=("id",),
        montant="qte_brique_tonne",
        seulement=(
            "id",
            "date",
            "recette",
            "type_produit",
            "poid_une_brique_kg",
            "qte_brique_produit_unit_wagon",
            "qte_brique_unite",
            "qte_brique_tonne",
            "ration_cuisson_cocke_kg_tonne",
        ),
    ),
)

TABLES_DEPILEUSE = (
    TableX3(
        nom="dechargement_wagons",
        cle=("Id",),
        seulement=(
            "Id",
            "date_heure_entree",
            "date_heure_sortie",
            "ordre_wagon",
            "numero_reel_wagon",
            "temps_decharge",
        ),
    ),
    TableX3(
        nom="donnes_dep",
        cle=("Id",),
        seulement=(
            "Id",
            "date_insert",
            "temps_max_dech_wagon",
            "temps_max_embal_paquet",
            "temps_max_soudage_paquet",
            "temps_max_cycle_paquet_embal",
        ),
    ),
    TableX3(
        nom="donnes_prod_dep",
        cle=("date_insert",),
        montant="wagon_depile",
        seulement=(
            "date_insert",
            "heure_marche",
            "heure_arret",
            "wagon_depile",
            "paquet_embale",
            "paquet_vrac",
        ),
    ),
)

COPIES = (
    ("usine_moulage", TABLES_MOULAGE, MOULAGE),
    ("usine_sechoir", TABLES_SECHOIR, SECHOIR),
    ("usine_empileuse", TABLES_EMPILEUSE, EMPILEUSE),
    ("usine_four", TABLES_FOUR, FOUR),
    ("usine_depileuse", TABLES_DEPILEUSE, DEPILEUSE),
)


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    parseur.add_argument("--complet", action="store_true", help="recopie entière des mesures")
    options = parseur.parse_args(arguments)

    from ingestion.rapprochement import rapprocher_tables

    conforme = True
    for nom_pipeline, tables, cible in COPIES:
        print(f"\n═══ {cible.base} ═══")
        charger(
            nom_pipeline,
            tables,
            simulation=options.simulation,
            complet=options.complet,
            cible=cible,
        )
        if not options.simulation:
            conforme &= rapprocher_tables(tables, cible)
    return 0 if conforme else 1


if __name__ == "__main__":
    sys.exit(main())
