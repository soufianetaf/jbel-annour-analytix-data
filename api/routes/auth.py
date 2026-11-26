"""Connexion : identifiant et mot de passe contre un jeton ; qui suis-je."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.base import Entrepot
from api.config import ParametresApi
from api.roles import DOMAINES
from api.securite import (
    Utilisateur,
    authentifier,
    creer_jeton,
    entrepot_api,
    parametres_api,
    utilisateur_courant,
)

routeur = APIRouter(prefix="/auth", tags=["connexion"])


class Jeton(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Moi(BaseModel):
    identifiant: str
    role: str
    domaines: list[str]


@routeur.post("/jeton", response_model=Jeton, summary="Se connecter")
def jeton(
    formulaire: Annotated[OAuth2PasswordRequestForm, Depends()],
    entrepot: Annotated[Entrepot, Depends(entrepot_api)],
    parametres: Annotated[ParametresApi, Depends(parametres_api)],
) -> Jeton:
    utilisateur = authentifier(entrepot, formulaire.username, formulaire.password)
    if utilisateur is None:
        # Même réponse que l'identifiant soit inconnu ou le mot de passe faux
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Jeton(access_token=creer_jeton(utilisateur, parametres))


@routeur.get("/moi", response_model=Moi, summary="Mon compte et les domaines auxquels j'ai droit")
def moi(utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)]) -> Moi:
    domaines = sorted(d for d, roles in DOMAINES.items() if utilisateur.role in roles)
    return Moi(identifiant=utilisateur.identifiant, role=utilisateur.role, domaines=domaines)
