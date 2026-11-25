"""Copie des applications du magasin (serveur de l'usine) vers l'entrepôt.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.usine_magasin --simulation   # contrôles, rien n'est lu
    uv run python -m ingestion.usine_magasin                # copie, puis rapprochement

    Magasin.dbo.requests              sorties magasin par service → raw_magasin.requests
    Magasin.dbo.requests_gazoil       bons de gasoil              → raw_magasin.requests_gazoil
    espace_magasin.dbo.demandes_achats         demandes d'achat   → raw_espace_magasin.…
    espace_magasin.dbo.demandes_achats_lignes  lignes de DA
    espace_magasin.dbo.depassement             dépassements de budget
    espace_magasin.dbo.requests_entry          entrées magasin
    espace_magasin.dbo.da_coke_fuel            silos de coke et de fuel

Serveur lu avec le compte « sa » (dérogation déclarée dans .env) : seules
des lectures sont faites, sans verrou. Toutes les tables sont petites
(moins de 20 000 lignes) : copie complète à chaque passage.

Jamais copiés (liste fermée) : mots de passe (table users), jetons de
validation (approval_tokens), codes PIN (utilisateurs_badges), CIN et
matricule des chauffeurs, noms des demandeurs et des personnes concernées,
signatures, commentaires et motifs en texte libre.
"""

from __future__ import annotations

import argparse
import sys

from ingestion.x3 import Cible, TableX3, charger

MAGASIN = Cible(source="usine", base="Magasin", schema_source="dbo", schema_raw="raw_magasin")
ESPACE_MAGASIN = Cible(
    source="usine", base="espace_magasin", schema_source="dbo", schema_raw="raw_espace_magasin"
)

TABLES_MAGASIN = (
    TableX3(
        nom="requests",
        cle=("id",),
        montant="quantity",
        seulement=(
            "id",
            "article",  # code article
            "designation",
            "quantity",  # quantité demandée
            "quantite_stock",
            "quantite_credit",
            "qte_robot_saisie",  # quantité saisie dans Sage X3 par le robot
            "service",  # service demandeur
            "service_concerne",  # service consommateur
            "affectation1",  # machine, zone…
            "affectation2",
            "affectation3",
            "affectation4",
            "intitule",
            "MS",
            "retour",
            "approval",  # décision
            "status",
            "created_at",
            "validated_at",
        ),
    ),
    # Bons de gasoil : CIN (cin), matricule et nom du demandeur NON copiés
    TableX3(
        nom="requests_gazoil",
        cle=("id",),
        montant="quantity",
        seulement=(
            "id",
            "article",
            "quantity",  # quantité de gasoil
            "qte_saisie",
            "service",
            "vehicule",
            "affectation_1",
            "affectation_2",
            "km_parcouru",
            "solde_j_1",
            "num_BR",  # numéro du bon
            "intitule",
            "nature",
            "approval",
            "status",
            "created_at",
            "validated_at",
        ),
    ),
)

TABLES_ESPACE_MAGASIN = (
    TableX3(
        nom="demandes_achats",
        cle=("id",),
        montant="quantite_val",
        # « depassement_buget » contient « PASS » : c'est un indicateur de
        # dépassement de budget, pas un mot de passe
        autorisees=frozenset({"depassement_buget"}),
        seulement=(
            "id",
            "numero",
            "da_no",  # numéro de la DA dans Sage X3
            "date",
            "echeance",
            "departement_demandeur",
            "service",
            "affectation2",
            "famille",
            "code_article",
            "quantite_val",  # quantité validée
            "fournisseur",
            "visa_demandeur",
            "visa_resp_magasin",
            "status",
            "decision",
            "depassement_buget",
            "validated_at",
            "created_at",
            "updated_at",
            "date_sys",
        ),
    ),
    TableX3(
        nom="demandes_achats_lignes",
        cle=("id",),
        montant="quantite",
        seulement=(
            "id",
            "demande_achat_id",
            "da_no",
            "code_article",
            "code_article_valide",
            "designation",
            "reference",
            "marque",
            "famille",
            "affectation",
            "quantite",
            "quantite_val",
            "status",
            "decision",
            "validated_at",
            "created_at",
            "updated_at",
        ),
    ),
    TableX3(
        nom="depassement",
        cle=("id",),
        montant="qte_demande",
        # « numero_depassemnt » contient « PASS » : numéro de dépassement
        autorisees=frozenset({"numero_depassemnt"}),
        seulement=(
            "id",
            "numero_depassemnt",
            "numero_da",
            "numero_budget",
            "type_da",
            "code_article",
            "designation",
            "famille",
            "marque",
            "qte_demande",
            "qte_buget",
            "qte_recomande",
            "date_creation",
            "date_aprove",
            "statut",
            "statut_RES_Magasin",
            "statut_RES_Methode",
            "statut_RES_dga",
            "statut_RES_gestion",
            "statut_RES_amelioration",
            "statut_RES_logistique",
            "statut_PDG",
            "accept_partiel",
        ),
    ),
    TableX3(
        nom="requests_entry",
        cle=("id",),
        montant="quantity",
        seulement=(
            "id",
            "type",
            "article",
            "designation",
            "item",
            "quantity",
            "service",
            "affectation1",
            "affectation2",
            "ME",
            "status",
            "validated_at",
            "created_at",
            "updated_at",
            "deleted_at",
        ),
    ),
    TableX3(
        nom="da_coke_fuel",
        cle=("id",),
        montant="total_silos_coke",
        seulement=(
            "id",
            "numero_da",
            "article",
            "marque",
            "affectation",
            "service",
            "status",
            "solde",
            "silo1",
            "silo2",
            "silo_fuel",
            "total_silos_coke",
            "bc",
            "br",
            "nb_relance",
            "date_cree",
            "update_date",
        ),
    ),
)

COPIES = (
    ("usine_magasin", TABLES_MAGASIN, MAGASIN),
    ("usine_espace_magasin", TABLES_ESPACE_MAGASIN, ESPACE_MAGASIN),
)


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    options = parseur.parse_args(arguments)

    from ingestion.rapprochement import rapprocher_tables

    conforme = True
    for nom_pipeline, tables, cible in COPIES:
        print(f"\n═══ {cible.base} ═══")
        charger(nom_pipeline, tables, simulation=options.simulation, cible=cible)
        if not options.simulation:
            conforme &= rapprocher_tables(tables, cible)
    return 0 if conforme else 1


if __name__ == "__main__":
    sys.exit(main())
