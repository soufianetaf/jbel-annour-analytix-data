"""Tableau de bord de la direction (marts.agg_direction_mois, docs/indicateurs/cout_revient.md)."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_api, exiger_domaine

routeur = APIRouter(prefix="/direction", tags=["direction"])


class MoisDirection(BaseModel):
    mois: date
    ca_net: float | None
    resultat: float | None
    tresorerie_fin_mois: float | None
    tonnes_cuites: float | None
    tonnes_briques_vendues: float | None
    cout_par_tonne: float | None
    cout_energie_par_tonne: float | None
    marge_briques: float | None
    kwh_par_tonne: float | None
    heures_arret_maintenance: float | None


@routeur.get(
    "/mois", response_model=list[MoisDirection], summary="Indicateurs de la direction par mois"
)
def mois(
    _: Annotated[Utilisateur, Depends(exiger_domaine("direction"))],
    entrepot: Annotated[Entrepot, Depends(entrepot_api)],
    p: Annotated[Periode, Depends(periode)],
) -> list[dict]:
    return entrepot.lire(
        """
        SELECT mois, ca_net, resultat, tresorerie_fin_mois, tonnes_cuites,
               tonnes_briques_vendues, cout_par_tonne, cout_energie_par_tonne,
               marge_briques, kwh_par_tonne, heures_arret_maintenance
        FROM marts.agg_direction_mois
        WHERE mois BETWEEN date_trunc('month', %(debut)s::date) AND %(fin)s
        ORDER BY mois
        """,
        {"debut": p.debut, "fin": p.fin},
    )
