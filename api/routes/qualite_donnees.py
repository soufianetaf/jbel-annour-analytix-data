"""Qualité des données : lignes à corriger par contrôle et par service.

Définitions : docs/indicateurs/qualite_donnees.md.

Seulement les comptages : le détail des lignes en erreur (schéma
qualite_donnees, données métier) n'est pas exposé.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.base import Entrepot
from api.securite import Utilisateur, entrepot_lecteur, exiger_domaine

routeur = APIRouter(prefix="/qualite-donnees", tags=["qualité des données"])


class Controle(BaseModel):
    test: str
    service: str | None
    correction: str | None
    statut: str
    dernier_controle_le: datetime
    lignes_en_erreur: int
    lignes_controle_precedent: int | None
    evolution: int | None
    premiere_erreur_le: datetime | None


@routeur.get("", response_model=list[Controle], summary="Contrôles de qualité des données")
def controles(
    _: Annotated[Utilisateur, Depends(exiger_domaine("qualite_donnees"))],
    entrepot: Annotated[Entrepot, Depends(entrepot_lecteur)],
    service: Annotated[str | None, Query(description="Seulement ce service")] = None,
) -> list[dict]:
    return entrepot.lire(
        """
        SELECT test, service, correction, statut, dernier_controle_le, lignes_en_erreur,
               lignes_controle_precedent, evolution, premiere_erreur_le
        FROM marts.agg_qualite_donnees
        WHERE (%(service)s::text IS NULL OR service = %(service)s)
        ORDER BY lignes_en_erreur DESC, test
        """,
        {"service": service},
    )
