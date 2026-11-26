"""API de Jbel Annour Analytix (FastAPI).

L'interface web (dépôt séparé) et les autres clients ne lisent jamais
l'entrepôt directement : ils passent par cette API, qui applique les rôles
côté serveur et journalise chaque accès. Le contrat entre les deux dépôts
est le schéma OpenAPI publié par l'API (/docs, /openapi.json).

Lancer en développement, depuis la racine du dépôt :

    uv run uvicorn api.main:app --reload
"""
