"""Copie des ventes de Sage X3 (factures, clients, articles) vers raw_x3.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.x3_ventes --simulation   # contrôles, rien n'est lu
    uv run python -m ingestion.x3_ventes                # copie, puis rapprochement

    BASE1.SINVOICE    entêtes de factures et d'avoirs → raw_x3.sinvoice
    BASE1.SINVOICED   lignes de factures et d'avoirs  → raw_x3.sinvoiced
    BASE1.BPCUSTOMER  fiches clients (liste fermée)   → raw_x3.bpcustomer
    BASE1.ITMMASTER   fiches articles (liste fermée)  → raw_x3.itmmaster

Tables de moins de 100 000 lignes : copie complète à chaque passage.
La mécanique (contrôles, dlt, traçabilité) est dans ingestion/x3.py.
"""

from __future__ import annotations

import sys

from ingestion.x3 import SCHEMA_RAW, TableX3, executer

NOM_PIPELINE = "x3_ventes"
__all__ = ["NOM_PIPELINE", "SCHEMA_RAW", "TABLES"]

TABLES = (
    TableX3(
        nom="SINVOICE",
        cle=("NUM_0",),
        montant="AMTATI_0",  # montant TTC de la facture
        exclues=frozenset({"PAYBAN_0"}),  # banque de paiement du client
    ),
    TableX3(
        nom="SINVOICED",
        cle=("NUM_0", "SIDLIN_0"),
        montant="AMTATILIN_0",  # montant TTC de la ligne
        # BPC INV = code du client facturé (pas un numéro de CIN)
        autorisees=frozenset({"BPCINV_0"}),
    ),
    # Fiche client : contient le CIN du gérant et de l'assuré (XCINGER_0,
    # XCINASS_0), la banque (PAYBAN_0) et des informations financières
    # maison. Liste fermée : seules les colonnes utiles à l'analyse.
    TableX3(
        nom="BPCUSTOMER",
        cle=("BPCNUM_0",),
        seulement=(
            "BPCNUM_0",  # code client
            "BPCNAM_0",  # raison sociale
            "BPCSHO_0",  # intitulé court
            "BCGCOD_0",  # catégorie client
            "GRP_0",  # groupe de clients
            "BPCTYP_0",  # type de client
            "BPCSTA_0",  # actif / inactif
            "CUR_0",  # devise
            "REP_0",  # représentant principal
            "REP_1",  # second représentant
            "PTE_0",  # condition de paiement
            "TSCCOD_0",  # familles statistiques client
            "TSCCOD_1",
            "TSCCOD_2",
            "TSCCOD_3",
            "TSCCOD_4",
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",  # numéro de ligne interne de X3, exigé par dlt (clé technique)
        ),
    ),
    # Fiche article : aucune colonne sensible, mais 256 colonnes dont
    # l'essentiel est technique. Liste fermée, pour la même raison.
    TableX3(
        nom="ITMMASTER",
        cle=("ITMREF_0",),
        seulement=(
            "ITMREF_0",  # code article
            "ITMDES1_0",  # désignation
            "ITMDES2_0",  # désignation complémentaire
            "TCLCOD_0",  # catégorie d'article
            "TSICOD_0",  # familles statistiques article
            "TSICOD_1",
            "TSICOD_2",
            "TSICOD_3",
            "TSICOD_4",
            "ITMSTA_0",  # statut
            "STU_0",  # unité de stock
            "SAU_0",  # unité de vente
            "SAUSTUCOE_0",  # coefficient unité de vente → unité de stock
            "WEU_0",  # unité de poids
            "ITMWEI_0",  # poids unitaire (servira aux tonnes vendues)
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",  # numéro de ligne interne de X3, exigé par dlt (clé technique)
        ),
    ),
)


if __name__ == "__main__":
    sys.exit(executer(NOM_PIPELINE, TABLES, __doc__.splitlines()[0]))
