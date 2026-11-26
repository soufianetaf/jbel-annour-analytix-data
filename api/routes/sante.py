"""État de l'API et de l'entrepôt. Seule route sans connexion : elle ne renvoie aucune donnée."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.base import Entrepot
from api.securite import entrepot_api

routeur = APIRouter(tags=["santé"])


class Sante(BaseModel):
    api: str
    entrepot: str


@routeur.get("/sante", response_model=Sante, summary="L'API et l'entrepôt répondent-ils ?")
def sante(entrepot: Annotated[Entrepot, Depends(entrepot_api)]) -> Sante:
    try:
        entrepot.lire("SELECT 1 AS ok")
        etat = "ok"
    except Exception:  # noqa: BLE001 - on dit seulement que l'entrepôt ne répond pas
        etat = "indisponible"
    return Sante(api="ok", entrepot=etat)
