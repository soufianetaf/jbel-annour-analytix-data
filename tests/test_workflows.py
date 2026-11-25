"""Les fichiers de la CI sont du YAML valide, avec la structure attendue par GitHub.

Pourquoi : un fichier de workflow invalide ne lance AUCUN contrôle. GitHub
affiche « Invalid workflow file » et la branche n'est plus protégée par la
CI. Ce test l'attrape avant le push, en local.
"""

from pathlib import Path

import pytest
import yaml

DOSSIER = Path(__file__).resolve().parents[1] / ".github" / "workflows"
WORKFLOWS = sorted(DOSSIER.glob("*.yml"))


def test_au_moins_un_workflow() -> None:
    assert WORKFLOWS, "aucun fichier dans .github/workflows"


@pytest.mark.parametrize("fichier", WORKFLOWS, ids=lambda f: f.name)
def test_workflow_lisible_et_complet(fichier: Path) -> None:
    contenu = yaml.safe_load(fichier.read_text(encoding="utf-8"))

    assert isinstance(contenu, dict)
    # PyYAML lit la clé « on » comme le booléen True (YAML 1.1)
    assert "on" in contenu or True in contenu, "déclencheurs (on:) manquants"
    assert contenu.get("jobs"), "aucun job"
    for nom, job in contenu["jobs"].items():
        assert "runs-on" in job, f"job {nom} : runs-on manquant"
        for etape in job.get("steps", []):
            assert "run" in etape or "uses" in etape, f"job {nom} : étape vide"
            if "run" in etape:
                assert isinstance(etape["run"], str), f"job {nom} : commande mal lue"
