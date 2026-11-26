"""Usine : production par poste, machines, énergie, qualité des briques.

Définitions : docs/indicateurs/production_postes.md, machines.md, energie.md, qualite.md.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_lecteur, exiger_domaine

routeur = APIRouter(tags=["production"])
Lecteur = Annotated[Utilisateur, Depends(exiger_domaine("production"))]
Base = Annotated[Entrepot, Depends(entrepot_lecteur)]
Dates = Annotated[Periode, Depends(periode)]


class ProductionZone(BaseModel):
    date_poste: date
    zone: str | None
    realise: float | None
    objectif: float | None
    taux_realisation: float | None


class MachineJour(BaseModel):
    machine: str
    jour: date
    production: float | None
    unite_production: str | None
    heures_marche: float | None
    heures_arret: float | None
    disponibilite: float | None


class EnergieJour(BaseModel):
    jour: date
    kwh_site: float | None
    electricite_complete: bool
    tonnes_cuites: float | None
    kwh_par_tonne: float | None
    coke_kg_par_tonne: float | None


class PrixElectricite(BaseModel):
    mois: date
    facture_electricite: float | None
    kwh_estimes: float | None
    prix_kwh_12_mois: float | None
    energie_reactive_excedentaire_kvarh: float | None
    penalite_cos_phi_estimee: float | None


class QualiteMois(BaseModel):
    mois: date
    chariots: int
    conformes: int
    defaut_mineur: int
    defaut_majeur: int
    non_controles: int


class PertesPoids(BaseModel):
    jour: date
    type_brique: str
    poids_mouleuse_kg: float | None
    poids_sechoir_kg: float | None
    poids_four_kg: float | None
    perte_sechage: float | None
    perte_cuisson: float | None


@routeur.get(
    "/production/postes",
    response_model=list[ProductionZone],
    summary="Réalisé et objectif par jour et par zone (fiches de poste retenues)",
)
def postes(_: Lecteur, entrepot: Base, p: Dates):
    return entrepot.lire(
        """
        SELECT date_poste, zone, sum(realise) AS realise, sum(objectif) AS objectif,
               sum(realise) / nullif(sum(objectif), 0) AS taux_realisation
        FROM marts.fct_production_poste
        WHERE date_poste BETWEEN %(debut)s AND %(fin)s
        GROUP BY date_poste, zone
        ORDER BY date_poste, zone
        """,
        {"debut": p.debut, "fin": p.fin},
    )


@routeur.get(
    "/machines/jour", response_model=list[MachineJour], summary="Bilan du jour de chaque machine"
)
def machines(_: Lecteur, entrepot: Base, p: Dates):
    return entrepot.lire(
        """
        SELECT machine, jour, production, unite_production,
               heures_marche, heures_arret, disponibilite
        FROM marts.fct_machines_jour
        WHERE jour BETWEEN %(debut)s AND %(fin)s
        ORDER BY jour, machine
        """,
        {"debut": p.debut, "fin": p.fin},
    )


@routeur.get(
    "/energie/jour",
    response_model=list[EnergieJour],
    summary="Électricité du site, tonnes cuites, kWh et coke par tonne",
)
def energie(_: Lecteur, entrepot: Base, p: Dates):
    return entrepot.lire(
        """
        SELECT jour, kwh_site, electricite_complete, tonnes_cuites, kwh_par_tonne, coke_kg_par_tonne
        FROM marts.agg_energie_jour
        WHERE jour BETWEEN %(debut)s AND %(fin)s
        ORDER BY jour
        """,
        {"debut": p.debut, "fin": p.fin},
    )


@routeur.get(
    "/energie/prix",
    response_model=list[PrixElectricite],
    summary="Facture d'électricité, prix du kWh sur 12 mois, énergie réactive",
)
def prix_electricite(_: Lecteur, entrepot: Base, p: Dates):
    return entrepot.lire(
        """
        SELECT mois, facture_electricite, kwh_estimes, prix_kwh_12_mois,
               energie_reactive_excedentaire_kvarh, penalite_cos_phi_estimee
        FROM marts.agg_electricite_prix_mois
        WHERE mois BETWEEN date_trunc('month', %(debut)s::date) AND %(fin)s
        ORDER BY mois
        """,
        {"debut": p.debut, "fin": p.fin},
    )


@routeur.get(
    "/qualite/chariots",
    response_model=list[QualiteMois],
    summary="Chariots contrôlés en sortie du four, par mois et par statut",
)
def chariots(_: Lecteur, entrepot: Base, p: Dates):
    return entrepot.lire(
        """
        SELECT date_trunc('month', jour)::date                                    AS mois,
               count(*)                                                           AS chariots,
               count(*) FILTER (WHERE statut_chariot = 'conforme')                AS conformes,
               count(*) FILTER (WHERE statut_chariot = 'défaut mineur')           AS defaut_mineur,
               count(*) FILTER (WHERE statut_chariot = 'défaut majeur')           AS defaut_majeur,
               count(*) FILTER (WHERE statut_chariot = 'non contrôlé')            AS non_controles
        FROM marts.fct_chariots_qualite
        WHERE jour BETWEEN %(debut)s AND %(fin)s
        GROUP BY 1
        ORDER BY 1
        """,
        {"debut": p.debut, "fin": p.fin},
    )


@routeur.get(
    "/qualite/pertes-poids",
    response_model=list[PertesPoids],
    summary="Poids des briques et pertes au séchage et à la cuisson",
)
def pertes_poids(_: Lecteur, entrepot: Base, p: Dates):
    return entrepot.lire(
        """
        SELECT jour, type_brique, poids_mouleuse_kg, poids_sechoir_kg, poids_four_kg,
               perte_sechage, perte_cuisson
        FROM marts.agg_pertes_poids_jour
        WHERE jour BETWEEN %(debut)s AND %(fin)s
        ORDER BY jour, type_brique
        """,
        {"debut": p.debut, "fin": p.fin},
    )


class PerformanceMachine(BaseModel):
    machine: str
    jour: date
    disponibilite: float | None
    performance: float | None
    trs_hors_qualite: float | None
    cadence_par_heure: float | None
    cadence_reference: float | None
    pannes: int
    minutes_arret_maintenance: int
    production_perdue_estimee: float | None
    unite_production: str | None


@routeur.get(
    "/machines/performance",
    response_model=list[PerformanceMachine],
    summary="TRS (hors qualité) et production perdue par les pannes, par machine et par jour",
)
def performance_machines(_: Lecteur, entrepot: Base, p: Dates):
    return entrepot.lire(
        """
        SELECT machine, jour, disponibilite, performance, trs_hors_qualite, cadence_par_heure,
               cadence_reference, pannes, minutes_arret_maintenance, production_perdue_estimee,
               unite_production
        FROM marts.agg_performance_machine_jour
        WHERE jour BETWEEN %(debut)s AND %(fin)s
        ORDER BY jour, machine
        """,
        {"debut": p.debut, "fin": p.fin},
    )


class ElectriciteMachine(BaseModel):
    compteur: str
    kwh: float | None
    kwh_par_tonne: float | None
    kwh_par_unite: float | None
    unite_production: str | None
    cos_phi_moyen: float | None
    energie_reactive_excedentaire_kvarh: float | None


@routeur.get(
    "/energie/machines",
    response_model=list[ElectriciteMachine],
    summary="Électricité de chaque machine sur la période : kWh, par tonne et par unité",
)
def electricite_machines(_: Lecteur, entrepot: Base, p: Dates):
    # Ratios sur la période : total des kWh / total des tonnes (ou de la production),
    # sur les seuls jours où les deux sont connus
    return entrepot.lire(
        """
        SELECT compteur,
               sum(kwh)                                                          AS kwh,
               sum(kwh) FILTER (WHERE tonnes_cuites_site > 0)
                   / nullif(sum(tonnes_cuites_site) FILTER (WHERE kwh IS NOT NULL), 0)
                   AS kwh_par_tonne,
               sum(kwh) FILTER (WHERE production_machine > 0)
                   / nullif(sum(production_machine) FILTER (WHERE kwh IS NOT NULL), 0)
                   AS kwh_par_unite,
               max(unite_production)                       AS unite_production,
               avg(cos_phi_moyen)                                                AS cos_phi_moyen,
               sum(energie_reactive_excedentaire_kvarh)
                   AS energie_reactive_excedentaire_kvarh
        FROM marts.agg_electricite_machine_jour
        WHERE jour BETWEEN %(debut)s AND %(fin)s
        GROUP BY compteur
        ORDER BY kwh_par_tonne DESC NULLS LAST
        """,
        {"debut": p.debut, "fin": p.fin},
    )
