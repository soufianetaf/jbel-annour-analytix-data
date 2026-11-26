"""Ventes : CA net par mois, meilleurs clients.

Source : marts.fct_ventes ; définitions : docs/indicateurs/ventes_ca_net.md.

Le représentant ne voit que SES ventes : le filtre est dans la requête SQL,
avec le code représentant de son compte. Un représentant sans code ne voit rien.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_api, exiger_domaine

routeur = APIRouter(prefix="/ventes", tags=["ventes"])
Lecteur = Annotated[Utilisateur, Depends(exiger_domaine("ventes"))]


def filtre_representant(utilisateur: Utilisateur) -> str | None:
    """Code représentant à imposer à la requête ; aucun pour les autres rôles."""
    if utilisateur.role != "representant":
        return None
    if not utilisateur.representant:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Compte représentant sans code représentant Sage X3"
        )
    return utilisateur.representant


class CaMois(BaseModel):
    mois: date
    ca_net: float
    factures: int


class CaClient(BaseModel):
    code_client: str | None
    nom_client: str | None
    ca_net: float


@routeur.get("/ca-mensuel", response_model=list[CaMois], summary="CA net HT par mois")
def ca_mensuel(
    utilisateur: Lecteur,
    entrepot: Annotated[Entrepot, Depends(entrepot_api)],
    p: Annotated[Periode, Depends(periode)],
) -> list[dict]:
    return entrepot.lire(
        """
        SELECT date_trunc('month', date_comptable)::date AS mois,
               sum(montant_ht_signe)                     AS ca_net,
               count(DISTINCT numero_facture)            AS factures
        FROM marts.fct_ventes
        WHERE date_comptable BETWEEN %(debut)s AND %(fin)s
          AND (%(representant)s::text IS NULL OR representant = %(representant)s)
        GROUP BY 1
        ORDER BY 1
        """,
        {"debut": p.debut, "fin": p.fin, "representant": filtre_representant(utilisateur)},
    )


@routeur.get("/clients", response_model=list[CaClient], summary="Meilleurs clients par CA net HT")
def meilleurs_clients(
    utilisateur: Lecteur,
    entrepot: Annotated[Entrepot, Depends(entrepot_api)],
    p: Annotated[Periode, Depends(periode)],
    limite: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[dict]:
    return entrepot.lire(
        """
        SELECT v.code_client, c.nom_client, sum(v.montant_ht_signe) AS ca_net
        FROM marts.fct_ventes AS v
        LEFT JOIN marts.dim_client AS c ON c.cle_client = v.cle_client
        WHERE v.date_comptable BETWEEN %(debut)s AND %(fin)s
          AND (%(representant)s::text IS NULL OR v.representant = %(representant)s)
        GROUP BY v.code_client, c.nom_client
        ORDER BY ca_net DESC
        LIMIT %(limite)s
        """,
        {
            "debut": p.debut,
            "fin": p.fin,
            "representant": filtre_representant(utilisateur),
            "limite": limite,
        },
    )


class CycleMois(BaseModel):
    mois: date
    livraisons: int
    montant_livre_ht: float | None
    livraisons_facturees: int
    jours_median_expedition_facture: float | None
    montant_livre_non_facture: float | None


class LivraisonNonFacturee(BaseModel):
    numero_livraison: str
    code_client: str | None
    nom_client: str | None
    date_expedition: date | None
    jours_sans_facture: int | None
    montant_ht: float | None


@routeur.get(
    "/cycle-mois",
    response_model=list[CycleMois],
    summary="Livraisons du mois, délai jusqu'à la facture, livré non facturé",
)
def cycle_mois(
    utilisateur: Lecteur,
    entrepot: Annotated[Entrepot, Depends(entrepot_api)],
    p: Annotated[Periode, Depends(periode)],
) -> list[dict]:
    # Lu dans fct_livraisons (pas agg_commercial_mois) : le représentant
    # ne doit voir que ses livraisons
    return entrepot.lire(
        """
        SELECT date_trunc('month', date_expedition)::date   AS mois,
               count(*)                                     AS livraisons,
               sum(montant_ht)                              AS montant_livre_ht,
               count(*) FILTER (WHERE est_facturee)         AS livraisons_facturees,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY jours_expedition_facture)
                   AS jours_median_expedition_facture,
               sum(montant_ht) FILTER (WHERE est_validee AND NOT est_facturee)
                   AS montant_livre_non_facture
        FROM marts.fct_livraisons
        WHERE date_expedition BETWEEN %(debut)s AND %(fin)s
          AND (%(representant)s::text IS NULL OR representant = %(representant)s)
        GROUP BY 1
        ORDER BY 1
        """,
        {"debut": p.debut, "fin": p.fin, "representant": filtre_representant(utilisateur)},
    )


@routeur.get(
    "/livre-non-facture",
    response_model=list[LivraisonNonFacturee],
    summary="Livraisons validées pas encore facturées, les plus anciennes d'abord",
)
def livre_non_facture(
    utilisateur: Lecteur,
    entrepot: Annotated[Entrepot, Depends(entrepot_api)],
    limite: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict]:
    return entrepot.lire(
        """
        SELECT l.numero_livraison, l.code_client, c.nom_client, l.date_expedition,
               l.jours_sans_facture, l.montant_ht
        FROM marts.fct_livraisons AS l
        LEFT JOIN marts.dim_client AS c ON c.cle_client = l.cle_client
        WHERE l.est_validee AND NOT l.est_facturee
          AND (%(representant)s::text IS NULL OR l.representant = %(representant)s)
        ORDER BY l.jours_sans_facture DESC NULLS LAST, l.montant_ht DESC
        LIMIT %(limite)s
        """,
        {"representant": filtre_representant(utilisateur), "limite": limite},
    )
