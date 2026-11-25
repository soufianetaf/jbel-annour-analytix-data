"""Les photos quotidiennes (dossier dbt/models/snapshots) ne peuvent jamais être effacées.

Pourquoi : une photo passée (stock, créances…) ne se recalcule pas. Sans
« full_refresh=false », la commande « dbt build --full-refresh »
reconstruirait la table et effacerait tout l'historique, sans prévenir.
Chaque nouvelle photo est contrôlée automatiquement par ce test.
"""

import re
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parents[1] / "dbt" / "models" / "snapshots"
PHOTOS = sorted(DOSSIER.glob("*.sql"))


def _config(sql: str) -> str:
    """Le texte de config(...) du modèle, sans les commentaires Jinja."""
    sans_commentaires = re.sub(r"\{#.*?#\}", "", sql, flags=re.DOTALL)
    return " ".join(re.findall(r"config\((.*?)\)\s*\}\}", sans_commentaires, flags=re.DOTALL))


def test_photos_trouvees() -> None:
    assert len(PHOTOS) >= 2


@pytest.mark.parametrize("photo", PHOTOS, ids=lambda f: f.stem)
def test_photo_jamais_reconstruite(photo: Path) -> None:
    config = _config(photo.read_text(encoding="utf-8"))

    assert re.search(r"full_refresh\s*=\s*false", config), "full_refresh=false manquant"
    assert "materialized='incremental'" in config
    # La photo du jour remplace celle du même jour, sans toucher aux autres
    assert "unique_key='date_photo'" in config
