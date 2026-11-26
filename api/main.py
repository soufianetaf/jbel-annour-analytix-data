"""Application FastAPI : assemble les routes, le journal des accès et le CORS."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.base import Entrepot, EntrepotPostgres
from api.config import ParametresApi
from api.journal import JournalAcces
from api.limites import LimiteurTentatives
from api.routes import (
    achats,
    auth,
    cout_revient,
    direction,
    finance,
    maintenance,
    production,
    qualite_donnees,
    rh,
    sante,
    ventes,
)
from api.securite_http import EnTetesSecurite

VERSION = "v1"
# Tous les routeurs de l'API, dans l'ordre. Les tests parcourent CETTE liste
# (et la comparent au schéma OpenAPI) pour vérifier les droits de chaque route.
ROUTEURS = (
    sante,
    auth,
    ventes,
    finance,
    achats,
    production,
    maintenance,
    cout_revient,
    direction,
    rh,
    qualite_donnees,
)


def creer_app(parametres: ParametresApi | None = None, entrepot: Entrepot | None = None) -> FastAPI:
    """L'application. Les tests passent leurs paramètres et un faux entrepôt."""
    parametres = parametres or ParametresApi()

    @asynccontextmanager
    async def cycle_de_vie(app: FastAPI):
        if entrepot is None:
            reel = EntrepotPostgres(parametres)
            reel.ouvrir()
            app.state.entrepot = reel
            yield
            reel.fermer()
        else:
            app.state.entrepot = entrepot
            yield

    # En production, la documentation interactive est fermée (API_DOCS=true la rouvre)
    docs = parametres.documentation_ouverte
    app = FastAPI(
        title="Jbel Annour Analytix",
        version="0.1.0",
        description=(
            "API de l'entrepôt de données de Jbel Annour. Chaque route est réservée "
            "à des rôles (api/roles.py) ; chaque accès est journalisé."
        ),
        lifespan=cycle_de_vie,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.parametres = parametres
    app.state.limiteur = LimiteurTentatives(
        par_compte=parametres.api_tentatives_par_compte,
        par_adresse=parametres.api_tentatives_par_adresse,
        fenetre_secondes=parametres.api_fenetre_tentatives_minutes * 60,
    )
    if entrepot is not None:
        app.state.entrepot = entrepot

    app.add_middleware(EnTetesSecurite)
    app.add_middleware(JournalAcces)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=parametres.origines_cors,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    for module in ROUTEURS:
        app.include_router(module.routeur, prefix=f"/{VERSION}")
    return app


def _configurer_journaux() -> None:
    gestionnaire = logging.StreamHandler()
    gestionnaire.setFormatter(logging.Formatter("%(message)s"))
    journal = logging.getLogger("analytix.acces")
    journal.addHandler(gestionnaire)
    journal.setLevel(logging.INFO)
    journal.propagate = False


def __getattr__(nom: str):
    # « uvicorn api.main:app » : l'application n'est construite (et .env lu)
    # qu'au lancement, pas à l'import du module (les tests importent sans .env)
    if nom == "app":
        _configurer_journaux()
        return creer_app()
    raise AttributeError(nom)
