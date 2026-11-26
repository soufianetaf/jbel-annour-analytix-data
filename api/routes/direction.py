"""Tableau de bord de la direction (marts.agg_direction_mois, docs/indicateurs/cout_revient.md)."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_lecteur, exiger_domaine

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
    entrepot: Annotated[Entrepot, Depends(entrepot_lecteur)],
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


class Alerte(BaseModel):
    code: str
    niveau: str  # critique, attention, information
    service: str
    titre: str
    detail: str
    valeur: float | None
    page: str  # page de l'interface où agir


ORDRE_NIVEAUX = {"critique": 0, "attention": 1, "information": 2}
LIBELLES_MACHINES = {
    "moulage": "du moulage",
    "empileuse": "de l'empileuse",
    "depileuse": "de la dépileuse",
}


def _mad(valeur: float) -> str:
    return f"{valeur / 1e6:.2f}".replace(".", ",") + " M MAD"


def _premiere(lignes: list[dict]) -> dict:
    """La ligne d'un agrégat ; un dictionnaire vide si la requête ne renvoie rien."""
    return lignes[0] if lignes else {}


def calculer_alertes(entrepot: Entrepot) -> list[Alerte]:
    """Les alertes du moment, chacune lue dans une table déjà rapprochée.

    Seules les alertes qui ont lieu d'être sont renvoyées (rien à signaler :
    liste vide). Seuils : docs/api.md, « Alertes de la direction ».
    """
    alertes: list[Alerte] = []

    lnf = _premiere(
        entrepot.lire(
            """
        SELECT count(*) AS livraisons, coalesce(sum(montant_ht), 0) AS montant,
               max(jours_sans_facture) AS plus_ancienne
        FROM marts.fct_livraisons
        WHERE est_validee AND NOT est_facturee
        """
        )
    )
    if lnf.get("livraisons"):
        ancien = lnf["plus_ancienne"] or 0
        alertes.append(
            Alerte(
                code="livre_non_facture",
                niveau="critique" if ancien > 45 else "attention" if ancien > 30 else "information",
                service="ADV",
                titre=f"{_mad(float(lnf['montant']))} livrés, pas encore facturés",
                detail=f"{lnf['livraisons']} livraisons, la plus ancienne depuis {ancien} jours",
                valeur=float(lnf["montant"]),
                page="ventes",
            )
        )

    soldees = _premiere(
        entrepot.lire(
            """
        SELECT count(*) AS commandes, coalesce(sum(montant_ht), 0) AS montant
        FROM marts.fct_commandes
        WHERE soldee_sans_livraison AND date_commande >= current_date - 365
        """
        )
    )
    if soldees.get("commandes"):
        alertes.append(
            Alerte(
                code="commandes_soldees_sans_livraison",
                niveau="attention",
                service="ADV",
                titre=f"{soldees['commandes']} commandes soldées sans livraison",
                detail=f"Sur 12 mois, {_mad(float(soldees['montant']))} : annulations ou doublons",
                valeur=float(soldees["commandes"]),
                page="ventes",
            )
        )

    # Une machine de la chaîne (le four cuit en continu) sans aucune heure de
    # marche sur 7 jours : son automate ne compte plus
    muettes = entrepot.lire(
        """
        SELECT machine
        FROM marts.fct_machines_jour
        WHERE jour > current_date - 7 AND machine <> 'four'
        GROUP BY machine
        HAVING coalesce(sum(heures_marche), 0) = 0
        ORDER BY machine
        """
    )
    for ligne in muettes:
        machine = LIBELLES_MACHINES.get(ligne["machine"], ligne["machine"])
        alertes.append(
            Alerte(
                code=f"automate_sans_heures_{ligne['machine']}",
                niveau="critique",
                service="Automatisme",
                titre=f"L'automate {machine} ne compte plus ses heures",
                detail="Aucune heure de marche sur 7 jours : ni TRS ni MTBF",
                valeur=None,
                page="production",
            )
        )

    cos_phi = entrepot.lire(
        """
        SELECT compteur, sum(energie_reactive_kvarh) / nullif(sum(kwh), 0) AS tan_phi
        FROM marts.fct_electricite_jour
        WHERE jour > current_date - 30 AND compteur IN ('transfo1', 'transfo2')
        GROUP BY compteur
        HAVING sum(energie_reactive_kvarh) / nullif(sum(kwh), 0) > 0.75
        """
    )
    for ligne in cos_phi:
        alertes.append(
            Alerte(
                code=f"cos_phi_{ligne['compteur']}",
                niveau="attention",
                service="Énergie",
                titre=f"cos φ sous 0,80 sur {ligne['compteur']}",
                detail="Sur 30 jours : risque de pénalités d'énergie réactive",
                valeur=float(ligne["tan_phi"]),
                page="production",
            )
        )

    qualite = _premiere(
        entrepot.lire(
            """
        SELECT coalesce(sum(lignes_en_erreur), 0) AS lignes, count(DISTINCT service) AS services
        FROM marts.agg_qualite_donnees
        WHERE lignes_en_erreur > 0
        """
        )
    )
    if qualite.get("lignes"):
        alertes.append(
            Alerte(
                code="qualite_donnees",
                niveau="information",
                service="Tous les services",
                titre=f"{qualite['lignes']} lignes à corriger dans les sources",
                detail=f"Dans {qualite['services']} services",
                valeur=float(qualite["lignes"]),
                page="qualite-donnees",
            )
        )

    return sorted(alertes, key=lambda a: (ORDRE_NIVEAUX[a.niveau], a.service))


@routeur.get(
    "/alertes",
    response_model=list[Alerte],
    summary="Ce que la direction doit surveiller aujourd'hui, du plus grave au moins grave",
)
def alertes(
    _: Annotated[Utilisateur, Depends(exiger_domaine("direction"))],
    entrepot: Annotated[Entrepot, Depends(entrepot_lecteur)],
) -> list[Alerte]:
    return calculer_alertes(entrepot)
