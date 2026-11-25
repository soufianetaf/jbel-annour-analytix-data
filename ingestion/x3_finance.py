"""Copie de la finance de Sage X3 (échéances, comptabilité) vers raw_x3.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.x3_finance --simulation   # contrôles, rien n'est lu
    uv run python -m ingestion.x3_finance                # copie incrémentale + rapprochement
    uv run python -m ingestion.x3_finance --complet      # copie entière (chaque semaine)

    BASE1.GACCDUDATE  échéances clients et fournisseurs → raw_x3.gaccdudate
    BASE1.GACCENTRYD  lignes d'écritures comptables     → raw_x3.gaccentryd
    BASE1.GACCENTRY   entêtes d'écritures comptables    → raw_x3.gaccentry
    BASE1.GACCOUNT    plan comptable                    → raw_x3.gaccount
    BASE1.FISCALYEAR  exercices comptables              → raw_x3.fiscalyear

Les échéances et les écritures dépassent 100 000 lignes et changent sans
cesse : copie incrémentale sur la date de modification, avec reprise des
3 derniers jours, et copie complète chaque semaine (cahier des charges,
8.4 a). Le plan comptable et les exercices sont recopiés en entier.
"""

from __future__ import annotations

import sys

from ingestion.x3 import TableX3, executer

NOM_PIPELINE = "x3_finance"

TABLES = (
    TableX3(
        nom="GACCDUDATE",
        cle=("TYP_0", "NUM_0", "LIG_0", "DUDLIG_0"),
        montant="AMTLOC_0",  # montant de l'échéance en monnaie de la société
        incremental="UPDDATTIM_0",
        lag_jours=3,
        # Liste fermée : la table ne contient pas de donnée sensible
        # repérée, mais 65 colonnes dont la moitié est technique.
        seulement=(
            "TYP_0",  # type de pièce comptable
            "NUM_0",  # numéro de pièce
            "LIG_0",  # ligne de la pièce
            "DUDLIG_0",  # numéro d'échéance
            "ACCNUM_0",  # numéro interne de l'écriture
            "CPY_0",  # société
            "FCY_0",  # site
            "CUR_0",  # devise
            "SAC_0",  # compte collectif (clients, fournisseurs…)
            "BPR_0",  # tiers
            "BPRTYP_0",  # type de tiers
            "BPRPAY_0",  # tiers payeur
            "DUDDAT_0",  # date d'échéance
            "PAM_0",  # mode de paiement
            "SNS_0",  # sens (1 ou -1)
            "AMTCUR_0",  # montant en devise
            "AMTLOC_0",  # montant en monnaie de la société
            "PAYCUR_0",  # payé, en devise
            "PAYLOC_0",  # payé, en monnaie de la société
            "TMPCUR_0",  # en cours de paiement, en devise
            "TMPLOC_0",  # en cours de paiement, en monnaie de la société
            "FLGCLE_0",  # indicateur de lettrage
            "PAYDAT_0",  # date de paiement
            "SOINUM_0",  # numéro du document d'origine (facture)
            "DUDSTA_0",  # statut de l'échéance
            "LEVFUP_0",  # niveau de relance
            "DATFUP_0",  # date de la dernière relance
            "FIY_0",  # exercice
            "PER_0",  # période
            "CREDATTIM_0",
            "UPDDATTIM_0",  # date de modification : sert à la copie incrémentale
            "ROWID",
        ),
    ),
    # ─── Comptabilité générale ─────────────────────────────────────
    # Lignes d'écritures : 600 000 lignes, incrémental. Libellé (DES_0) et
    # nom du tiers (XBPRNAM_0) NON copiés : un libellé peut contenir un nom
    # de personne. La paie est comptabilisée par compte, sans tiers salarié
    # (contrôlé le 25/11/2026 ; un test dbt le revérifie à chaque chargement).
    TableX3(
        nom="GACCENTRYD",
        cle=("TYP_0", "NUM_0", "LIN_0", "LEDTYP_0"),
        montant="AMTLED_0",  # montant en monnaie du registre (MAD)
        incremental="UPDDATTIM_0",
        seulement=(
            "TYP_0",  # type de pièce
            "NUM_0",  # numéro de pièce
            "LIN_0",  # ligne
            "LEDTYP_0",  # registre : 1 général, 2 analytique
            "ACCNUM_0",  # numéro interne de l'écriture
            "CPY_0",  # société
            "FCYLIN_0",  # site de la ligne
            "ACCDAT_0",  # date comptable
            "FIY_0",  # exercice
            "PER_0",  # période
            "COA_0",  # plan comptable
            "SAC_0",  # compte collectif
            "ACC_0",  # compte
            "BPR_0",  # tiers
            "SNS_0",  # sens : 1 débit, -1 crédit
            "CUR_0",  # devise
            "AMTCUR_0",  # montant en devise
            "AMTLED_0",  # montant en monnaie du registre (MAD)
            "QTY_0",  # quantité
            "UOM_0",  # unité
            "FLGMTC_0",  # lettrage
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
    # Entêtes d'écritures : journal, catégorie (réelle / simulation), statut
    TableX3(
        nom="GACCENTRY",
        cle=("TYP_0", "NUM_0"),
        incremental="UPDDATTIM_0",
        seulement=(
            "TYP_0",
            "NUM_0",
            "CPY_0",
            "FCY_0",
            "JOU_0",  # journal
            "FIY_0",
            "PER_0",
            "ACCDAT_0",
            "CAT_0",  # catégorie : 1 réelle, 2 et 3 à confirmer (simulation…)
            "STA_0",  # statut : 1 provisoire, 2 définitive
            "CUR_0",
            "ORIMOD_0",  # module d'origine (ventes, achats…)
            "RVS_0",  # extourne
            "BPRVCR_0",  # référence du document du tiers
            "CREDATTIM_0",
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
    # Plan comptable : 1 104 comptes, copie complète
    TableX3(
        nom="GACCOUNT",
        cle=("COA_0", "ACC_0"),
        seulement=(
            "COA_0",
            "ACC_0",
            "DES_0",  # intitulé du compte
            "DESSHO_0",
            "SAC_0",
            "CLSCOD_0",  # code de classement
            "ENAFLG_0",  # actif
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
    # Exercices comptables : dates de début et de fin
    TableX3(
        nom="FISCALYEAR",
        cle=("CPY_0", "LEDTYP_0", "FIYNUM_0"),
        seulement=(
            "CPY_0",
            "LEDTYP_0",
            "FIYNUM_0",
            "DES_0",
            "FIYSTR_0",
            "FIYEND_0",
            "FIYSTA_0",  # statut : ouvert, clôturé
            "UPDDATTIM_0",
            "ROWID",
        ),
    ),
)


if __name__ == "__main__":
    sys.exit(executer(NOM_PIPELINE, TABLES, __doc__.splitlines()[0]))
