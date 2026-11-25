"""Les fichiers YAML du projet dbt sont valides, et aucune description n'a été coupée.

Deux pièges YAML, rencontrés pendant le projet :
- « Grain : une ligne » sans guillemets : le « : » ouvre une nouvelle clé
  et le fichier devient illisible (dbt refuse de démarrer) ;
- dans une ligne { … }, une virgule coupe la description : la fin de la
  phrase devient une clé fantôme, sans erreur visible.
"""

from pathlib import Path

import pytest
import yaml

DOSSIER_DBT = Path(__file__).resolve().parents[1] / "dbt"
FICHIERS = sorted(
    f
    for f in DOSSIER_DBT.rglob("*.yml")
    if not {"dbt_packages", "target", "logs"} & set(f.parts) and f.name != ".user.yml"
)


def _cles_fantomes(objet, chemin=""):
    """Clés qui ressemblent à un morceau de phrase : contiennent une espace, sans valeur."""
    if isinstance(objet, dict):
        for cle, valeur in objet.items():
            if isinstance(cle, str) and " " in cle and valeur is None:
                yield f"{chemin}/{cle}"
            yield from _cles_fantomes(valeur, f"{chemin}/{cle}")
    elif isinstance(objet, list):
        for i, element in enumerate(objet):
            yield from _cles_fantomes(element, f"{chemin}[{i}]")


def test_fichiers_trouves() -> None:
    assert FICHIERS


@pytest.mark.parametrize("fichier", FICHIERS, ids=lambda f: str(f.relative_to(DOSSIER_DBT)))
def test_yaml_dbt_valide_sans_description_coupee(fichier: Path) -> None:
    contenu = yaml.safe_load(fichier.read_text(encoding="utf-8"))

    assert list(_cles_fantomes(contenu)) == [], "description coupée : mettre entre guillemets"


def test_detection_d_une_description_coupee() -> None:
    # Le cas réel : la virgule a coupé « Catégorie (TCLCOD_0), code X3. »
    texte = "- {name: categorie, description: Catégorie (TCLCOD_0), code X3.}"

    assert list(_cles_fantomes(yaml.safe_load(texte))) == ["[0]/code X3."]
