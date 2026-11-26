"""Achats et stock : factures fournisseurs, meilleurs fournisseurs, stock valorisé.

Définitions : docs/indicateurs/achats_circuit.md, stock_valorise.md.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.base import Entrepot
from api.routes.commun import Periode, periode
from api.securite import Utilisateur, entrepot_api, exiger_domaine

routeur = APIRouter(tags=["achats et stock"])
Lecteur = Annotated[Utilisateur, Depends(exiger_domaine("achats"))]
Base = Annotated[Entrepot, Depends(entrepot_api)]


class AchatsMois(BaseModel):
    mois: date
    montant_ht_mad: float
    factures: int
    fournisseurs: int


class AchatsFournisseur(BaseModel):
    code_fournisseur: str | None
    nom_fournisseur: str | None
    montant_ht_mad: float


class StockSite(BaseModel):
    site: str | None
    articles: int
    valeur_stock: float
    articles_dormants: int
    valeur_dormante: float


class StockArticle(BaseModel):
    code_article: str | None
    site: str | None
    stock_physique: float | None
    cmup: float | None
    valeur_stock: float | None
    est_dormant: bool | None


@routeur.get("/achats/mois", response_model=list[AchatsMois], summary="Achats facturés par mois")
def achats_mois(_: Lecteur, entrepot: Base, p: Annotated[Periode, Depends(periode)]):
    return entrepot.lire(
        """
        SELECT date_trunc('month', date_comptable)::date AS mois,
               sum(montant_ht_mad_signe)                 AS montant_ht_mad,
               count(DISTINCT numero_facture)            AS factures,
               count(DISTINCT code_fournisseur)          AS fournisseurs
        FROM marts.fct_achats_factures
        WHERE date_comptable BETWEEN %(debut)s AND %(fin)s
        GROUP BY 1
        ORDER BY 1
        """,
        {"debut": p.debut, "fin": p.fin},
    )


@routeur.get(
    "/achats/fournisseurs",
    response_model=list[AchatsFournisseur],
    summary="Meilleurs fournisseurs par montant facturé",
)
def fournisseurs(
    _: Lecteur,
    entrepot: Base,
    p: Annotated[Periode, Depends(periode)],
    limite: Annotated[int, Query(ge=1, le=200)] = 20,
):
    return entrepot.lire(
        """
        SELECT a.code_fournisseur, f.nom_fournisseur, sum(a.montant_ht_mad_signe) AS montant_ht_mad
        FROM marts.fct_achats_factures AS a
        LEFT JOIN marts.dim_fournisseur AS f ON f.cle_fournisseur = a.cle_fournisseur
        WHERE a.date_comptable BETWEEN %(debut)s AND %(fin)s
        GROUP BY a.code_fournisseur, f.nom_fournisseur
        ORDER BY montant_ht_mad DESC
        LIMIT %(limite)s
        """,
        {"debut": p.debut, "fin": p.fin, "limite": limite},
    )


@routeur.get("/stock/sites", response_model=list[StockSite], summary="Stock valorisé par site")
def stock_sites(_: Lecteur, entrepot: Base):
    return entrepot.lire(
        """
        SELECT site,
               count(*)                                         AS articles,
               coalesce(sum(valeur_stock), 0)                   AS valeur_stock,
               count(*) FILTER (WHERE est_dormant)              AS articles_dormants,
               coalesce(sum(valeur_stock) FILTER (WHERE est_dormant), 0) AS valeur_dormante
        FROM marts.fct_stock_article
        GROUP BY site
        ORDER BY valeur_stock DESC
        """
    )


@routeur.get(
    "/stock/articles",
    response_model=list[StockArticle],
    summary="Articles au plus fort stock valorisé",
)
def stock_articles(
    _: Lecteur,
    entrepot: Base,
    site: Annotated[str | None, Query(description="Seulement ce site")] = None,
    limite: Annotated[int, Query(ge=1, le=500)] = 50,
):
    return entrepot.lire(
        """
        SELECT code_article, site, stock_physique, cmup, valeur_stock, est_dormant
        FROM marts.fct_stock_article
        WHERE (%(site)s::text IS NULL OR site = %(site)s)
        ORDER BY valeur_stock DESC NULLS LAST
        LIMIT %(limite)s
        """,
        {"site": site, "limite": limite},
    )


class EquilibreMois(BaseModel):
    mois: date
    tonnes_cuites: float | None
    production_declaree: float | None
    livraisons: float | None
    tonnes_vendues: float | None
    stock_fin_mois: float | None


@routeur.get(
    "/stock/equilibre-briques",
    response_model=list[EquilibreMois],
    summary="Briques produites, stockées et vendues, en tonnes, par mois",
)
def equilibre_briques(_: Lecteur, entrepot: Base, p: Annotated[Periode, Depends(periode)]):
    return entrepot.lire(
        """
        SELECT mois, tonnes_cuites, production_declaree, livraisons, tonnes_vendues, stock_fin_mois
        FROM marts.agg_equilibre_briques_mois
        WHERE mois BETWEEN date_trunc('month', %(debut)s::date) AND %(fin)s
        ORDER BY mois
        """,
        {"debut": p.debut, "fin": p.fin},
    )
