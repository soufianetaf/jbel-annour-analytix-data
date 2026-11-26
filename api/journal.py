"""Journal des accès (cahier des charges : journal des accès et des exports).

Une ligne JSON par requête, sur le journal « analytix.acces » : qui, quel
rôle, quelle route, quels filtres, quel résultat, combien de temps. Jamais
de mot de passe ni de jeton : le corps des requêtes et l'en-tête
Authorization ne sont pas écrits.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

journal_acces = logging.getLogger("analytix.acces")


class JournalAcces(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        debut = time.perf_counter()
        statut = 500
        try:
            reponse = await call_next(request)
            statut = reponse.status_code
            return reponse
        finally:
            utilisateur = getattr(request.state, "utilisateur", None)
            journal_acces.info(
                json.dumps(
                    {
                        "le": datetime.now(UTC).isoformat(timespec="seconds"),
                        "utilisateur": utilisateur.identifiant if utilisateur else None,
                        "role": utilisateur.role if utilisateur else None,
                        "methode": request.method,
                        "chemin": request.url.path,
                        "filtres": dict(request.query_params),
                        "statut": statut,
                        "duree_ms": round((time.perf_counter() - debut) * 1000, 1),
                        "client": request.client.host if request.client else None,
                    },
                    ensure_ascii=False,
                )
            )
