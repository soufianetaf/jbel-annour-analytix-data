"""Copie de la finance de Sage X3 (échéances) vers raw_x3.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.x3_finance --simulation   # contrôles, rien n'est lu
    uv run python -m ingestion.x3_finance                # copie incrémentale + rapprochement
    uv run python -m ingestion.x3_finance --complet      # copie entière (chaque semaine)

    BASE1.GACCDUDATE  échéances clients et fournisseurs → raw_x3.gaccdudate

GACCDUDATE dépasse 100 000 lignes et change sans cesse (chaque règlement
modifie une échéance) : copie incrémentale sur la date de modification,
avec reprise des 3 derniers jours, et copie complète chaque semaine
(cahier des charges, 8.4 a).
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
)


if __name__ == "__main__":
    sys.exit(executer(NOM_PIPELINE, TABLES, __doc__.splitlines()[0]))
