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
