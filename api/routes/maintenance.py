"""Maintenance : préventif et interventions par zone, interventions les plus longues.

Définitions : docs/indicateurs/maintenance.md.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_lecteur, exiger_domaine

routeur = APIRouter(prefix="/maintenance", tags=["maintenance"])
Lecteur = Annotated[Utilisateur, Depends(exiger_domaine("maintenance"))]
Base = Annotated[Entrepot, Depends(entrepot_lecteur)]


class ZoneJour(BaseModel):
    zone: str
    jour: date
    tournees_faites: int
    points_controle: int
    points_non_conformes: int
    taux_realisation: float | None
    taux_conformite: float | None
    interventions: int
    minutes_intervention: int
    minutes_arret: int


class Intervention(BaseModel):
    jour: date
    zone: str | None
    equipement: str | None
    etat_machine: str | None
    type_panne: str | None
    type_intervention: str | None
    duree_minutes: int | None
    minutes_arret: int | None
    pieces: int


@routeur.get(
    "/zones",
    response_model=list[ZoneJour],
    summary="Préventif et interventions par zone et par jour",
)
def zones(
    _: Lecteur,
    entrepot: Base,
    p: Annotated[Periode, Depends(periode)],
    zone: Annotated[str | None, Query(description="Seulement cette zone (four, séchoir…)")] = None,
):
    return entrepot.lire(
        """
        SELECT zone, jour, tournees_faites, points_controle, points_non_conformes,
               taux_realisation, taux_conformite, interventions, minutes_intervention, minutes_arret
        FROM marts.agg_maintenance_zone_jour
        WHERE jour BETWEEN %(debut)s AND %(fin)s
          AND (%(zone)s::text IS NULL OR zone = %(zone)s)
        ORDER BY jour, zone
        """,
        {"debut": p.debut, "fin": p.fin, "zone": zone},
    )


@routeur.get(
    "/interventions",
    response_model=list[Intervention],
    summary="Interventions sur panne, les plus longues machine à l'arrêt d'abord",
)
def interventions(
    _: Lecteur,
    entrepot: Base,
    p: Annotated[Periode, Depends(periode)],
    zone: Annotated[str | None, Query()] = None,
    limite: Annotated[int, Query(ge=1, le=500)] = 100,
):
    return entrepot.lire(
        """
        SELECT jour, zone, equipement, etat_machine, type_panne, type_intervention,
               duree_minutes, minutes_arret, pieces
        FROM marts.fct_interventions_maintenance
        WHERE jour BETWEEN %(debut)s AND %(fin)s
          AND (%(zone)s::text IS NULL OR zone = %(zone)s)
        ORDER BY minutes_arret DESC NULLS LAST, duree_minutes DESC NULLS LAST
        LIMIT %(limite)s
        """,
        {"debut": p.debut, "fin": p.fin, "zone": zone, "limite": limite},
    )


class FiabiliteMois(BaseModel):
    zone: str
    mois: date
    pannes: int
    minutes_arret: int
    heures_marche: float | None
    mttr_minutes: float | None
    mtbf_heures: float | None


@routeur.get(
    "/fiabilite",
    response_model=list[FiabiliteMois],
    summary="Pannes, MTTR et MTBF par zone et par mois",
)
def fiabilite(_: Lecteur, entrepot: Base, p: Annotated[Periode, Depends(periode)]):
    return entrepot.lire(
        """
        SELECT zone, mois, pannes, minutes_arret, heures_marche, mttr_minutes, mtbf_heures
        FROM marts.agg_fiabilite_zone_mois
        WHERE mois BETWEEN date_trunc('month', %(debut)s::date) AND %(fin)s
        ORDER BY mois, zone
        """,
        {"debut": p.debut, "fin": p.fin},
    )
