"""Orchestration de Jbel Annour Analytix (Dagster).

Lancer l'interface, depuis la racine du dépôt :

    uv run dagster dev -m orchestration

puis ouvrir http://localhost:3000. Détail : docs/orchestration.md
"""

from orchestration.definitions import defs

__all__ = ["defs"]
