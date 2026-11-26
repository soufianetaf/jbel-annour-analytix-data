"""En-têtes de sécurité HTTP, sur chaque réponse de l'API.

- nosniff : le navigateur ne devine pas le type d'une réponse ;
- DENY / frame-ancestors : l'API ne s'affiche dans aucun cadre (clickjacking) ;
- no-referrer : l'adresse de l'API (et ses filtres) ne fuit pas vers d'autres sites ;
- no-store : les données ne restent pas dans le cache du navigateur ou d'un proxy ;
- CSP « default-src 'none' » : une réponse JSON ne charge rien. La page
  /docs (développement seulement) charge l'interface Swagger : elle en est
  exemptée.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

PAGES_DOCUMENTATION = ("/docs", "/redoc")

EN_TETES = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}
POLITIQUE_CONTENU = "default-src 'none'; frame-ancestors 'none'"


class EnTetesSecurite(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        reponse = await call_next(request)
        for nom, valeur in EN_TETES.items():
            reponse.headers.setdefault(nom, valeur)
        if not request.url.path.startswith(PAGES_DOCUMENTATION):
            reponse.headers.setdefault("Content-Security-Policy", POLITIQUE_CONTENU)
        return reponse
