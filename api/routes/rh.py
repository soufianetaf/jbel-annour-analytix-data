"""RH agrégée : effectifs et présence (docs/indicateurs/rh.md). Aucune donnée individuelle."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_api, exiger_domaine

routeur = APIRouter(prefix="/rh", tags=["rh"])
Lecteur = Annotated[Utilisateur, Depends(exiger_domaine("rh"))]


class EffectifService(BaseModel):
    service: str
    effectif_rh: int | None
    embauches_12_mois: int | None
    effectif_pointeuse: int | None


class PresenceJour(BaseModel):
    jour: date
    personnes_presentes: int
    effectif_pointeuse: int | None
    taux_presence: float | None
    heures_moyennes_site: float | None


@routeur.get("/effectifs", response_model=list[EffectifService], summary="Effectif par service")
def effectifs(_: Lecteur, entrepot: Annotated[Entrepot, Depends(entrepot_api)]) -> list[dict]:
    return entrepot.lire(
        """
        SELECT service, effectif_rh, embauches_12_mois, effectif_pointeuse
        FROM marts.fct_effectifs_service
        ORDER BY coalesce(effectif_rh, 0) + coalesce(effectif_pointeuse, 0) DESC
        """
    )


@routeur.get(
    "/presence", response_model=list[PresenceJour], summary="Présence sur le site par jour"
)
def presence(
    _: Lecteur,
    entrepot: Annotated[Entrepot, Depends(entrepot_api)],
    p: Annotated[Periode, Depends(periode)],
) -> list[dict]:
    return entrepot.lire(
        """
        SELECT jour, personnes_presentes, effectif_pointeuse, taux_presence, heures_moyennes_site
        FROM marts.agg_presence_jour
        WHERE jour BETWEEN %(debut)s AND %(fin)s
        ORDER BY jour
        """,
        {"debut": p.debut, "fin": p.fin},
    )
