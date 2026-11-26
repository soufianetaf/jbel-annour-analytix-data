"""Copie des commandes et livraisons clients de Sage X3 vers raw_x3.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.x3_commandes --simulation   # contrôles, rien n'est lu
    uv run python -m ingestion.x3_commandes                # copie, puis rapprochement

    BASE1.SORDER      entêtes de commandes clients      → raw_x3.sorder
    BASE1.SORDERQ     lignes de commandes (quantités)   → raw_x3.sorderq
    BASE1.SORDERP     lignes de commandes (prix)        → raw_x3.sorderp
    BASE1.SDELIVERY   entêtes de livraisons             → raw_x3.sdelivery
    BASE1.SDELIVERYD  lignes de livraisons              → raw_x3.sdeliveryd

Tables d'environ 70 000 lignes : copie complète à chaque passage.

Listes fermées : jamais les adresses, noms de contacts et de destinataires,
le chauffeur, les plaques, les remarques en texte libre, les utilisateurs
X3, ni le coût de revient des lignes (CPRPRI, faux : cahier des charges).
"""

from __future__ import annotations

import sys

from ingestion.x3 import SCHEMA_RAW, TableX3, executer

NOM_PIPELINE = "x3_commandes"
__all__ = ["NOM_PIPELINE", "SCHEMA_RAW", "TABLES"]

TABLES = (
    TableX3(
        nom="SORDER",
        cle=("SOHNUM_0",),
        montant="ORDNOT_0",  # montant HT de la commande
        autorisees=frozenset({"BPCINV_0"}),  # client facturé (pas un numéro de CIN)
        seulement=(
            "SOHNUM_0",  # numéro de commande
            "CPY_0",  # société
            "SOHTYP_0",  # type de commande
            "SOHCAT_0",  # catégorie
            "SALFCY_0",  # site de vente
            "BPCORD_0",  # client commandeur
            "BPCINV_0",  # client facturé
            "ORDDAT_0",  # date de commande
            "DEMDLVDAT_0",  # date de livraison demandée
            "SHIDAT_0",  # date d'expédition prévue
            "REP_0",  # représentant
            "CUR_0",  # devise
            "ORDSTA_0",  # statut : ouverte, soldée
            "DLVSTA_0",  # livraison : non livrée, partielle, livrée
            "INVSTA_0",  # facturation : non facturée, partielle, facturée
            "HLDSTA_0",  # blocage
            "LASDLVDAT_0",  # date de la dernière livraison
            "LASINVDAT_0",  # date de la dernière facture
            "ORDNOT_0",  # montant HT
            "ORDATI_0",  # montant TTC
            "LINNBR_0",  # nombre de lignes
            "CLELINNBR_0",  # lignes soldées
            "DLVLINNBR_0",  # lignes livrées
            "INVLINNBR_0",  # lignes facturées
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",  # numéro de ligne interne de X3, exigé par dlt (clé technique)
        ),
    ),
    TableX3(
        nom="SORDERQ",
        cle=("SOHNUM_0", "SOPLIN_0", "SOQSEQ_0"),
        montant="QTY_0",
        seulement=(
            "SOHNUM_0",
            "SOPLIN_0",  # ligne
            "SOQSEQ_0",  # séquence
            "ITMREF_0",  # article
            "STOFCY_0",  # site de stock
            "ORDDAT_0",
            "DEMDLVDAT_0",
            "SHIDAT_0",
            "SOQSTA_0",  # statut de la ligne
            "QTY_0",  # quantité commandée (unité de vente)
            "QTYSTU_0",  # quantité commandée (unité de stock)
            "ALLQTY_0",  # quantité allouée
            "DLVQTY_0",  # quantité livrée
            "INVQTY_0",  # quantité facturée
            "ODLQTY_0",  # quantité en cours de livraison
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
    TableX3(
        nom="SORDERP",
        cle=("SOHNUM_0", "SOPLIN_0", "SOPSEQ_0"),
        montant="NETPRINOT_0",
        seulement=(
            "SOHNUM_0",
            "SOPLIN_0",
            "SOPSEQ_0",
            "ITMREF_0",
            "REP1_0",  # représentant de la ligne
            "GROPRI_0",  # prix brut
            "NETPRI_0",  # prix net
            "NETPRINOT_0",  # prix net HT
            "SAU_0",  # unité de vente
            "SAUSTUCOE_0",
            "LINTYP_0",  # type de ligne
            "FOCFLG_0",  # gratuit
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
    TableX3(
        nom="SDELIVERY",
        cle=("SDHNUM_0",),
        montant="DLVNOT_0",
        autorisees=frozenset({"BPCINV_0"}),
        seulement=(
            "SDHNUM_0",  # numéro de livraison
            "CPY_0",
            "SDHTYP_0",
            "SDHCAT_0",
            "SALFCY_0",
            "STOFCY_0",
            "SOHNUM_0",  # commande d'origine
            "BPCORD_0",
            "BPCINV_0",
            "REP_0",
            "SHIDAT_0",  # date d'expédition
            "DLVDAT_0",  # date de livraison
            "CFMFLG_0",  # livraison validée
            "INVFLG_0",  # livraison facturée
            "SIHNUM_0",  # facture
            "DLVNOT_0",  # montant HT
            "NETWEI_0",  # poids net
            "WEU_0",  # unité de poids
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
    TableX3(
        nom="SDELIVERYD",
        cle=("SDHNUM_0", "SDDLIN_0"),
        montant="QTY_0",
        seulement=(
            "SDHNUM_0",
            "SDDLIN_0",
            "SOHNUM_0",
            "SOPLIN_0",
            "SOQSEQ_0",
            "ITMREF_0",
            "STOFCY_0",
            "SHIDAT_0",
            "QTY_0",  # quantité livrée (unité de vente)
            "QTYSTU_0",
            "RTNQTY_0",  # quantité retournée
            "NETPRINOT_0",
            "SAU_0",
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
