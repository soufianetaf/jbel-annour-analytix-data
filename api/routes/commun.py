"""Paramètres communs aux routes : la période demandée."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Annotated

from fastapi import HTTPException, Query, status

DUREE_MAX = timedelta(days=366 * 10)


@dataclass(frozen=True)
class Periode:
    debut: date
    fin: date


def periode(
    debut: Annotated[
        date | None,
        Query(description="Premier jour inclus (AAAA-MM-JJ) ; par défaut, un an avant la fin"),
    ] = None,
    fin: Annotated[
        date | None, Query(description="Dernier jour inclus (AAAA-MM-JJ) ; par défaut, aujourd'hui")
    ] = None,
) -> Periode:
    fin = fin or date.today()
    debut = debut or fin - timedelta(days=365)
    if debut > fin:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "debut doit précéder fin")
    if fin - debut > DUREE_MAX:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "période limitée à 10 ans")
    return Periode(debut, fin)
