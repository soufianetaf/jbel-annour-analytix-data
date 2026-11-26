"""Copie de la maintenance (serveur de l'usine) vers l'entrepôt.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.usine_maintenance --simulation
    uv run python -m ingestion.usine_maintenance

Base maintenance_2026, schéma maintenance : maintenance préventive
    equipements, actions, equipement_actions   équipements et points de contrôle
    rapports, rapports_quotidiens              tournées de contrôle par zone et poste
    resultats_controle                         résultat de chaque point (C, NC, vide)
    ordre_travail                              ordres de travail ouverts sur un NC
Base maintenance_2026, schéma dbo : interventions sur panne
    interventions, lignes_intervention         fiches et lignes d'intervention
Base maintenance, schéma dbo : demandes d'intervention (saisies seulement là)
    demandes_intervention

Les contrôles préventifs de l'ancienne base « maintenance » ne sont pas lus :
maintenance_2026 est l'application en service (2 118 tournées contre 378) et
les deux bases n'ont aucune fiche en commun (vérifié le 26/11/2026).
suivi_interventions n'est pas lu : ses 407 fiches sont toutes dans
interventions.

Jamais copiés : les noms d'intervenants et de contrôleurs, les identifiants
des utilisateurs, les commentaires, anomalies, causes, constats et travaux
en texte libre, les signatures.
"""

from __future__ import annotations

import argparse
import sys

from ingestion.x3 import Cible, TableX3, charger

PREVENTIF = Cible(
    source="usine",
    base="maintenance_2026",
    schema_source="maintenance",
    schema_raw="raw_maintenance",
)
INTERVENTIONS = Cible(
    source="usine",
    base="maintenance_2026",
    schema_source="dbo",
    schema_raw="raw_maintenance_interventions",
)
DEMANDES = Cible(
    source="usine", base="maintenance", schema_source="dbo", schema_raw="raw_maintenance_demandes"
)

TABLES_PREVENTIF = (
    TableX3(
        nom="equipements",
        cle=("id",),
        seulement=("id", "nom", "ordre", "codeE_sage", "created_at", "updated_at"),
    ),
    TableX3(nom="actions", cle=("id",), seulement=("id", "description", "created_at")),
    TableX3(
        nom="equipement_actions",
        cle=("id",),
        seulement=("id", "equipement_id", "action_id", "ordre", "created_at"),
    ),
    TableX3(
        nom="rapports",
        cle=("id",),
        seulement=("id", "type", "shift", "created_at"),  # type = zone
    ),
    TableX3(
        nom="rapports_quotidiens",
        cle=("id",),
        seulement=(
            "id",
            "rapport_id",
            "equipe",  # A, B, C, D
            "date_controle",
            "statut",
            "created_at",
            "updated_at",
        ),
    ),
    TableX3(
        nom="resultats_controle",
        cle=("id",),
        montant="quantite",
        seulement=(
            "id",
            "rapport_quotidien_id",
            "equipement_action_id",
            "statut",  # C conforme, NC non conforme, Empty non rempli
            "priorite",
            "type",
            "nature",
            "nc_type",
            "n_ot",
            "code_article",
            "quantite",
            "created_at",
            "updated_at",
        ),
    ),
    TableX3(
        nom="ordre_travail",
        cle=("id",),
        montant="quantite",
        seulement=(
            "id",
            "equipement_action_id",
            "rapport_quotidien_id",
            "numéro_ot",  # orthographe de la source
            "statut",
            "priorite",
            "type",
            "nature",
            "temps",  # temps prévu, saisi en texte
            "code_article",
            "quantite",
            "created_at",
            "updated_at",
        ),
    ),
)

TABLES_INTERVENTIONS = (
    TableX3(
        nom="interventions",
        cle=("id",),
        seulement=(
            "id",
            "numero_fiche",
            "date_fiche",
            "zone",
            "service_maintenance",
            "equipe",
            "shift",
            "created_at",
            "updated_at",
        ),
    ),
    TableX3(
        nom="lignes_intervention",
        cle=("id",),
        montant="qte",
        seulement=(
            "id",
            "intervention_id",
            "date_ligne",
            "equipement_ensemble",  # équipement concerné
            "etat_machine",  # ARR, EM, TM
            "type_panne",
            "type_intervention",  # curatif, palliatif
            "debut",
            "fin",
            "duree",  # saisie en texte, contrôle de debut / fin
            "code_article_pdr",  # pièces de rechange (JSON)
            "qte",
            "numero_ot",
            "created_at",
            "updated_at",
        ),
    ),
)

TABLES_DEMANDES = (
    TableX3(
        nom="demandes_intervention",
        cle=("id",),
        montant="compteur_machine",
        seulement=(
            "id",
            "service",
            "machine",
            "code_machine",
            "etat_machine",
            "compteur_machine",
            "urgence",  # +, ++, +++
            "type_intervention",
            "action_efficace",
            "statut",
            "date_heure_panne",
            "date_heure_debut",
            "date_heure_remise_service",
            "created_at",
            "updated_at",
        ),
    ),
)

COPIES = (
    ("usine_maintenance_preventif", TABLES_PREVENTIF, PREVENTIF),
    ("usine_maintenance_interventions", TABLES_INTERVENTIONS, INTERVENTIONS),
    ("usine_maintenance_demandes", TABLES_DEMANDES, DEMANDES),
)


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    options = parseur.parse_args(arguments)

    from ingestion.rapprochement import rapprocher_tables

    conforme = True
    for nom_pipeline, tables, cible in COPIES:
        print(f"\n═══ {cible.base}.{cible.schema_source} ═══")
        charger(nom_pipeline, tables, simulation=options.simulation, cible=cible)
        if not options.simulation:
            conforme &= rapprocher_tables(tables, cible)
    return 0 if conforme else 1


if __name__ == "__main__":
    sys.exit(main())
