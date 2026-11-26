"""Finance : compte de résultat, créances clients, trésorerie.

Définitions : docs/indicateurs/finance_compte_de_resultat.md,
finance_creances.md, finance_tresorerie.md.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_api, exiger_domaine

routeur = APIRouter(prefix="/finance", tags=["finance"])
Lecteur = Annotated[Utilisateur, Depends(exiger_domaine("finance"))]
Base = Annotated[Entrepot, Depends(entrepot_api)]


class LigneCpc(BaseModel):
    mois: date
    rubrique_cpc: str | None
    montant: float


class Creances(BaseModel):
    tranche_retard: str | None
    echeances: int
    reste_a_payer: float


class Tresorerie(BaseModel):
    famille: str | None
    solde: float


@routeur.get(
    "/compte-de-resultat",
    response_model=list[LigneCpc],
    summary="Compte de résultat par mois et par rubrique (produit positif, charge négative)",
)
def compte_de_resultat(_: Lecteur, entrepot: Base, p: Annotated[Periode, Depends(periode)]):
    return entrepot.lire(
        """
        SELECT mois, rubrique_cpc, sum(montant_resultat) AS montant
        FROM marts.agg_compte_de_resultat_mois
        WHERE mois BETWEEN date_trunc('month', %(debut)s::date) AND %(fin)s
        GROUP BY mois, rubrique_cpc
        ORDER BY mois, rubrique_cpc
        """,
        {"debut": p.debut, "fin": p.fin},
    )


@routeur.get(
    "/creances",
    response_model=list[Creances],
    summary="Créances clients ouvertes, par tranche de retard (balance âgée)",
)
def creances(_: Lecteur, entrepot: Base):
    return entrepot.lire(
        """
        SELECT tranche_retard, count(*) AS echeances, sum(reste_a_payer) AS reste_a_payer
        FROM marts.fct_echeances
        WHERE est_ouverte AND type_tiers = 'client'
        GROUP BY tranche_retard
        ORDER BY tranche_retard
        """
    )


@routeur.get(
    "/tresorerie",
    response_model=list[Tresorerie],
    summary="Position de trésorerie par famille de comptes à une date",
)
def tresorerie(
    _: Lecteur,
    entrepot: Base,
    jour: Annotated[
        date | None, Query(description="Date de la position ; par défaut, aujourd'hui")
    ] = None,
):
    # Dernier solde de chaque compte dans l'exercice de la date demandée
    return entrepot.lire(
        """
        SELECT famille, sum(solde_fin_jour) AS solde
        FROM (
            SELECT DISTINCT ON (cle_compte) famille, solde_fin_jour
            FROM marts.agg_tresorerie_jour
            WHERE date_jour <= %(jour)s
              AND extract(year FROM date_jour) = extract(year FROM %(jour)s::date)
            ORDER BY cle_compte, date_jour DESC
        ) AS comptes
        GROUP BY famille
        ORDER BY famille
        """,
        {"jour": jour or date.today()},
    )
