"""État de l'API et de l'entrepôt. Seule route sans connexion.

Elle ne renvoie aucune donnée métier : l'état de l'entrepôt et l'heure du
dernier chargement (pour l'en-tête « Données au … » de l'interface).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.base import Entrepot
from api.securite import entrepot_api

routeur = APIRouter(tags=["santé"])

# Dernier chargement = la copie la MOINS récente parmi Sage X3 et l'usine :
# toutes les données affichées sont au moins aussi fraîches que cette heure.
# Pas de fct_ventes, fct_livraisons ni fct_commandes : la sécurité par ligne
# n'y montre rien sans périmètre, et cette route n'a pas d'utilisateur.
TABLES_FRAICHEUR = (
    "fct_ecritures",  # Sage X3, finance
    "fct_stock_article",  # Sage X3, stock
    "fct_production_poste",  # usine, production
    "fct_machines_jour",  # usine, automates
    "fct_gasoil",  # usine, magasin
)
SQL_DERNIER_CHARGEMENT = (
    "SELECT min(dernier) AS dernier_chargement FROM ("
    + " UNION ALL ".join(
        f"SELECT max(charge_le) AS dernier FROM marts.{table}" for table in TABLES_FRAICHEUR
    )
    + ") AS copies"
)


class Sante(BaseModel):
    api: str
    entrepot: str
    dernier_chargement: datetime | None = None


@routeur.get("/sante", response_model=Sante, summary="L'API et l'entrepôt répondent-ils ?")
def sante(entrepot: Annotated[Entrepot, Depends(entrepot_api)]) -> Sante:
    try:
        lignes = entrepot.lire(SQL_DERNIER_CHARGEMENT)
    except Exception:  # noqa: BLE001 - on dit seulement que l'entrepôt ne répond pas
        return Sante(api="ok", entrepot="indisponible")
    dernier = lignes[0].get("dernier_chargement") if lignes else None
    return Sante(api="ok", entrepot="ok", dernier_chargement=dernier)
