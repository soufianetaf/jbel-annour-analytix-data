"""Copie du stock de Sage X3 (stock par article et site, mouvements) vers raw_x3.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.x3_stock --simulation   # contrôles, rien n'est lu
    uv run python -m ingestion.x3_stock                # copie incrémentale + rapprochement
    uv run python -m ingestion.x3_stock --complet      # copie entière (chaque semaine)

    BASE1.ITMMVT  stock et coût moyen par article × site → raw_x3.itmmvt
    BASE1.STOJOU  journal des mouvements de stock        → raw_x3.stojou

ITMMVT (14 000 lignes) est recopiée en entier : c'est l'état actuel du
stock, photographié chaque jour par dbt. STOJOU (1,2 million de lignes)
est copiée en incrémental sur la date de modification.
"""

from __future__ import annotations

import sys

from ingestion.x3 import TableX3, executer

NOM_PIPELINE = "x3_stock"

TABLES = (
    TableX3(
        nom="ITMMVT",
        cle=("ITMREF_0", "STOFCY_0"),
        montant="PHYSTO_0",  # quantité physique (rapprochement en quantité)
        seulement=(
            "ITMREF_0",  # article
            "STOFCY_0",  # site de stockage
            "PHYSTO_0",  # stock physique
            "CTLSTO_0",  # stock en contrôle qualité
            "REJSTO_0",  # stock rejeté
            "GLOALL_0",  # quantité allouée (réservée)
            "ORDSTO_0",  # quantité commandée (en attente de réception)
            "AVC_0",  # coût moyen unitaire pondéré (CMUP)
            "LASPURPRI_0",  # dernier prix d'achat
            "LASPURDAT_0",  # date du dernier achat
            "LASRCPPRI_0",  # dernier prix de réception
            "LASRCPDAT_0",  # date de la dernière réception
            "LASISSDAT_0",  # date de la dernière sortie
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
    # Journal des mouvements. Libellé (MVTDES_0) et champs libres (USRFLD*)
    # non copiés : texte libre, qui peut contenir un nom de personne.
    TableX3(
        nom="STOJOU",
        cle=("STOFCY_0", "UPDCOD_0", "ITMREF_0", "IPTDAT_0", "MVTSEQ_0", "MVTIND_0"),
        montant="AMTVAL_0",  # valeur du mouvement
        incremental="UPDDATTIM_0",
        seulement=(
            "STOFCY_0",  # site
            "UPDCOD_0",  # code de mise à jour
            "ITMREF_0",  # article
            "IPTDAT_0",  # date d'imputation du mouvement
            "MVTSEQ_0",  # séquence
            "MVTIND_0",  # indice
            "TRSTYP_0",  # type de mouvement
            "TRSFAM_0",  # famille de transaction
            "WRH_0",  # dépôt
            "LOC_0",  # emplacement
            "BPRNUM_0",  # tiers (fournisseur, client)
            "VCRTYP_0",  # type de document d'origine
            "VCRNUM_0",  # numéro du document d'origine
            "VCRLIN_0",  # ligne du document d'origine
            "QTYSTU_0",  # quantité en unité de stock (+ entrée, - sortie)
            "STU_0",  # unité de stock
            "AMTVAL_0",  # valeur du mouvement
            "PRIVAL_0",  # prix de valorisation
            "STA_0",  # statut du stock
            "CCE_0",  # sections analytiques (service, centre de coût…)
            "CCE_1",
            "CCE_2",
            "CCE_3",
            "CCE_4",
            "ACCDAT_0",  # date comptable
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
)


def main(arguments: list[str] | None = None) -> int:
    return executer(NOM_PIPELINE, TABLES, __doc__.splitlines()[0], arguments)


if __name__ == "__main__":
    sys.exit(main())
