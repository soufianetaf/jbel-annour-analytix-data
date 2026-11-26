"""Connexion des utilisateurs et contrôle d'accès, côté serveur.

- Mot de passe : jamais stocké, seulement son empreinte Argon2 (api.utilisateurs).
- Jeton : JWT signé par API_SECRET_KEY, valable API_DUREE_JETON_MINUTES.
- À CHAQUE requête, le compte est relu dans l'entrepôt : un compte désactivé
  ou changé de rôle perd ses droits tout de suite, sans attendre la fin du jeton.
- Chaque route déclare son domaine (exiger_domaine) ; api/roles.py dit qui y a droit.

Connexion par l'annuaire de l'entreprise (Active Directory) : prévue quand
il sera disponible (README, questions ouvertes) ; seule la vérification du
mot de passe changera.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from api.base import Entrepot
from api.config import ParametresApi
from api.roles import peut_lire

ALGORITHME = "HS256"
_hacheur = PasswordHasher()
# Empreinte d'un mot de passe quelconque : vérifiée quand l'identifiant est
# inconnu, pour que la réponse prenne le même temps (on ne devine pas les comptes)
_EMPREINTE_LEURRE = _hacheur.hash("aucun-compte-ne-porte-ce-mot-de-passe")

schema_oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/jeton")

REQUETE_COMPTE = """
    SELECT identifiant, empreinte_mot_de_passe, role, representant, actif
    FROM api.utilisateurs
    WHERE identifiant = %(identifiant)s
"""


@dataclass(frozen=True)
class Utilisateur:
    identifiant: str
    role: str
    representant: str | None = None


def empreinte(mot_de_passe: str) -> str:
    return _hacheur.hash(mot_de_passe)


def mot_de_passe_correct(empreinte_stockee: str, mot_de_passe: str) -> bool:
    try:
        return _hacheur.verify(empreinte_stockee, mot_de_passe)
    except (VerificationError, InvalidHashError):
        return False


def authentifier(entrepot: Entrepot, identifiant: str, mot_de_passe: str) -> Utilisateur | None:
    """Le compte, si l'identifiant existe, est actif et le mot de passe est le bon."""
    lignes = entrepot.lire(REQUETE_COMPTE, {"identifiant": identifiant.strip().lower()})
    if not lignes:
        mot_de_passe_correct(_EMPREINTE_LEURRE, mot_de_passe)
        return None
    compte = lignes[0]
    if not mot_de_passe_correct(compte["empreinte_mot_de_passe"], mot_de_passe):
        return None
    if not compte["actif"]:
        return None
    return Utilisateur(compte["identifiant"], compte["role"], compte["representant"])


def creer_jeton(utilisateur: Utilisateur, parametres: ParametresApi) -> str:
    maintenant = datetime.now(UTC)
    contenu = {
        "sub": utilisateur.identifiant,
        "iat": maintenant,
        "exp": maintenant + timedelta(minutes=parametres.api_duree_jeton_minutes),
    }
    return jwt.encode(contenu, parametres.api_secret_key.get_secret_value(), ALGORITHME)


# ─── Dépendances FastAPI ─────────────────────────────────────────────


def parametres_api(request: Request) -> ParametresApi:
    return request.app.state.parametres


def entrepot_api(request: Request) -> Entrepot:
    return request.app.state.entrepot


_REFUS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Connexion requise ou expirée",
    headers={"WWW-Authenticate": "Bearer"},
)


def utilisateur_courant(
    request: Request,
    jeton: Annotated[str, Depends(schema_oauth2)],
    parametres: Annotated[ParametresApi, Depends(parametres_api)],
    entrepot: Annotated[Entrepot, Depends(entrepot_api)],
) -> Utilisateur:
    try:
        contenu = jwt.decode(
            jeton,
            parametres.api_secret_key.get_secret_value(),
            algorithms=[ALGORITHME],
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.PyJWTError as erreur:
        raise _REFUS from erreur
    # Le compte est relu : désactivé ou supprimé, il perd ses droits tout de suite
    lignes = entrepot.lire(REQUETE_COMPTE, {"identifiant": contenu["sub"]})
    if not lignes or not lignes[0]["actif"]:
        raise _REFUS
    compte = lignes[0]
    utilisateur = Utilisateur(compte["identifiant"], compte["role"], compte["representant"])
    request.state.utilisateur = utilisateur  # pour le journal des accès
    return utilisateur


def exiger_domaine(domaine: str):
    """Dépendance : l'utilisateur doit avoir droit au domaine (api/roles.py), sinon 403."""

    def verifier(
        utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)],
    ) -> Utilisateur:
        if not peut_lire(utilisateur.role, domaine):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Le rôle « {utilisateur.role} » n'a pas accès au domaine « {domaine} »",
            )
        return utilisateur

    verifier.domaine = domaine  # lu par les tests : chaque route déclare son domaine
    return verifier
