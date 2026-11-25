"""Copie des achats de Sage X3 (circuit demande → commande → réception → facture).

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.x3_achats --simulation   # contrôles, rien n'est lu
    uv run python -m ingestion.x3_achats                # copie, puis rapprochement

    BASE1.PREQUIS     entêtes de demandes d'achat   → raw_x3.prequis
    BASE1.PREQUISD    lignes de demandes d'achat    → raw_x3.prequisd
    BASE1.PREQUISO    lien demande → commande       → raw_x3.prequiso
    BASE1.PORDER      entêtes de commandes          → raw_x3.porder
    BASE1.PORDERQ     lignes de commandes           → raw_x3.porderq
    BASE1.PRECEIPTD   lignes de réceptions          → raw_x3.preceiptd
    BASE1.PINVOICE    entêtes de factures fournisseurs → raw_x3.pinvoice
    BASE1.PINVOICED   lignes de factures fournisseurs  → raw_x3.pinvoiced
    BASE1.BPSUPPLIER  fiches fournisseurs           → raw_x3.bpsupplier

Toutes ces tables font moins de 100 000 lignes : copie complète à chaque
passage. Listes fermées partout : ni banque du fournisseur, ni nom ou
adresse des tiers sur les documents, ni texte libre.
"""

from __future__ import annotations

import sys

from ingestion.x3 import TableX3, executer

NOM_PIPELINE = "x3_achats"

_SUIVI = ("CREDATTIM_0", "UPDDATTIM_0", "ROWID")

TABLES = (
    TableX3(
        nom="PREQUIS",
        cle=("PSHNUM_0",),
        seulement=(
            "PSHNUM_0",  # numéro de la demande d'achat
            "CPY_0",
            "PSHFCY_0",  # site demandeur
            "PRQDAT_0",  # date de la demande
            "CCE_0",  # section analytique : service demandeur
            "REQUSR_0",  # code utilisateur du demandeur
            "APPFLG_0",  # signée (approuvée)
            "ORDFLG_0",  # transformée en commande
            "CLEFLG_0",  # soldée
            *_SUIVI,
        ),
    ),
    TableX3(
        nom="PREQUISD",
        cle=("PSHNUM_0", "PSDLIN_0"),
        montant="LINAMT_0",
        seulement=(
            "PSHNUM_0",
            "PSDLIN_0",  # ligne
            "PSHFCY_0",
            "ITMREF_0",  # article
            "BPSNUM_0",  # fournisseur proposé
            "QTYSTU_0",  # quantité demandée (unité de stock)
            "ORDQTYSTU_0",  # quantité commandée
            "STU_0",
            "CUR_0",
            "NETPRI_0",  # prix net
            "LINAMT_0",  # montant HT de la ligne
            "EXTRCPDAT_0",  # date de réception souhaitée
            "LINORDFLG_0",  # ligne commandée
            "LINCLEFLG_0",  # ligne soldée
            "LINAPPFLG_0",  # ligne signée
            *_SUIVI,
        ),
    ),
    # Lien demande d'achat → commande. Dans Sage X3, les lignes de commande
    # n'ont PAS de référence à la DA (champs d'origine vides) : le lien est
    # dans cette table, une ligne par (ligne de DA, ligne de commande).
    TableX3(
        nom="PREQUISO",
        cle=("PSHNUM_0", "PSDLIN_0", "POHNUM_0", "POPLIN_0", "POQSEQ_0"),
        montant="QTYSTU_0",
        seulement=(
            "PSHNUM_0",
            "PSDLIN_0",
            "POHNUM_0",
            "POPLIN_0",
            "POQSEQ_0",
            "QTYSTU_0",  # quantité commandée à partir de la DA
            "STU_0",
            *_SUIVI,
        ),
    ),
    TableX3(
        nom="PORDER",
        cle=("POHNUM_0",),
        montant="TOTLINAMT_0",
        seulement=(
            "POHNUM_0",  # numéro de commande
            "CPY_0",
            "POHFCY_0",  # site commandeur
            "POHTYP_0",  # type de commande
            "PURTYP_0",  # type d'achat
            "ORDDAT_0",  # date de commande
            "BPSNUM_0",  # fournisseur
            "BUY_0",  # acheteur
            "CCE_0",  # section analytique
            "CUR_0",
            "APPFLG_0",  # signée
            "RCPFLG_0",  # reçue
            "INVFLG_0",  # facturée
            "CLEFLG_0",  # soldée
            "TOTLINAMT_0",  # montant HT des lignes
            "TOTLINQTY_0",
            *_SUIVI,
        ),
    ),
    TableX3(
        nom="PORDERQ",
        cle=("POHNUM_0", "POPLIN_0", "POQSEQ_0"),
        montant="LINAMT_0",
        seulement=(
            "POHNUM_0",
            "POPLIN_0",  # ligne
            "POQSEQ_0",  # échéance de livraison
            "POHFCY_0",
            "ORDDAT_0",
            "BPSNUM_0",
            "ITMREF_0",
            "QTYSTU_0",  # quantité commandée (unité de stock)
            "RCPQTYSTU_0",  # quantité reçue
            "INVQTYSTU_0",  # quantité facturée
            "RETQTYSTU_0",  # quantité retournée
            "STU_0",
            "EXTRCPDAT_0",  # date de réception prévue
            "LASRCPDAT_0",  # date de la dernière réception
            "LASINVDAT_0",  # date de la dernière facture
            "LINAMT_0",  # montant HT de la ligne
            "NETCUR_0",  # devise
            "LINSTA_0",  # statut de la ligne
            "LINCLEFLG_0",  # ligne soldée
            "VCRTYPORI_0",  # document d'origine (ex. demande d'achat)
            "VCRNUMORI_0",
            "VCRLINORI_0",
            *_SUIVI,
        ),
    ),
    TableX3(
        nom="PRECEIPTD",
        cle=("PTHNUM_0", "PTDLIN_0"),
        montant="LINAMT_0",
        seulement=(
            "PTHNUM_0",  # numéro de réception
            "PTDLIN_0",  # ligne
            "PRHFCY_0",  # site de réception
            "RCPDAT_0",  # date de réception
            "POHNUM_0",  # commande d'origine
            "POPLIN_0",
            "POQSEQ_0",
            "BPSNUM_0",
            "ITMREF_0",
            "QTYSTU_0",  # quantité reçue
            "RTNQTYSTU_0",  # quantité retournée
            "STU_0",
            "NETPRI_0",
            "LINAMT_0",
            "NETCUR_0",
            *_SUIVI,
        ),
    ),
    TableX3(
        nom="PINVOICE",
        cle=("NUM_0",),
        montant="AMTNOT_0",
        seulement=(
            "NUM_0",  # numéro de facture
            "INVTYP_0",  # 1 facture, 2 avoir…
            "PIVTYP_0",  # type de facture
            "BPR_0",  # fournisseur
            "CPY_0",
            "FCY_0",
            "ACCDAT_0",  # date comptable
            "BPRDAT_0",  # date de la facture du fournisseur
            "STA_0",  # statut
            "SNS_0",  # sens
            "CUR_0",
            "AMTNOT_0",  # montant HT
            "AMTATI_0",  # montant TTC
            "AMTNOTL_0",  # montant HT en monnaie de la société
            "STRDUDDAT_0",  # départ de l'échéance
            *_SUIVI,
        ),
    ),
    TableX3(
        nom="PINVOICED",
        cle=("NUM_0", "PIDLIN_0"),
        montant="AMTNOTLIN_0",
        seulement=(
            "NUM_0",
            "PIDLIN_0",  # ligne
            "INVTYP_0",
            "FCYLIN_0",
            "ACCDAT_0",
            "BPR_0",
            "ITMREF_0",
            "QTYSTU_0",
            "STU_0",
            "NETPRI_0",  # prix net unitaire
            "AMTNOTLIN_0",  # montant HT de la ligne
            "NETCUR_0",
            "POHNUM_0",  # commande d'origine
            "POPLIN_0",
            "POQSEQ_0",
            "PTHNUM_0",  # réception d'origine
            "PTDLIN_0",
            *_SUIVI,
        ),
    ),
    # Fiche fournisseur : la banque (PAYBAN_0) n'est pas copiée
    TableX3(
        nom="BPSUPPLIER",
        cle=("BPSNUM_0",),
        seulement=(
            "BPSNUM_0",  # code fournisseur
            "BPSNAM_0",  # raison sociale
            "BPSSHO_0",
            "BPSTYP_0",  # type de fournisseur
            "BPSGRU_0",  # groupe
            "CUR_0",
            "ACCCOD_0",  # code comptable
            "ENAFLG_0",  # actif
            *_SUIVI,
        ),
    ),
)


if __name__ == "__main__":
    sys.exit(executer(NOM_PIPELINE, TABLES, __doc__.splitlines()[0]))
