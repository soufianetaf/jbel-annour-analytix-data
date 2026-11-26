"""Coût de revient par tonne et marge par type de brique.

Définitions : docs/indicateurs/cout_revient.md. Le chiffre à lire est le
coût sur 12 mois glissants ; le coût d'un mois seul est donné pour le détail.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_api, exiger_domaine

routeur = APIRouter(prefix="/cout-revient", tags=["coût de revient"])
Lecteur = Annotated[Utilisateur, Depends(exiger_domaine("cout_revient"))]
Base = Annotated[Entrepot, Depends(entrepot_api)]


class CoutMois(BaseModel):
    mois: date
    charges_production: float | None
    tonnes_cuites: float | None
    cout_par_tonne_12_mois: float | None
    cout_energie_par_tonne_12_mois: float | None
    cout_par_tonne_mois: float | None


class MargeType(BaseModel):
    mois: date
    type_brique: str
    tonnes_vendues: float | None
    ca_ht: float | None
    prix_par_tonne: float | None
    cout_par_tonne: float | None
    marge_par_tonne: float | None
    marge: float | None


@routeur.get("/mois", response_model=list[CoutMois], summary="Coût de revient par tonne cuite")
def mois(_: Lecteur, entrepot: Base, p: Annotated[Periode, Depends(periode)]):
    return entrepot.lire(
        """
        SELECT mois, charges_production, tonnes_cuites, cout_par_tonne_12_mois,
               cout_energie_par_tonne_12_mois, cout_par_tonne_mois
        FROM marts.agg_cout_revient_mois
        WHERE mois BETWEEN date_trunc('month', %(debut)s::date) AND %(fin)s
        ORDER BY mois
        """,
        {"debut": p.debut, "fin": p.fin},
    )


@routeur.get(
    "/marges", response_model=list[MargeType], summary="Prix, coût et marge par tonne et par type"
)
def marges(_: Lecteur, entrepot: Base, p: Annotated[Periode, Depends(periode)]):
    return entrepot.lire(
        """
        SELECT mois, type_brique, tonnes_vendues, ca_ht, prix_par_tonne, cout_par_tonne,
               marge_par_tonne, marge
        FROM marts.agg_marge_type_brique_mois
        WHERE mois BETWEEN date_trunc('month', %(debut)s::date) AND %(fin)s
        ORDER BY mois, type_brique
        """,
        {"debut": p.debut, "fin": p.fin},
    )
