"""Chaque avertissement dbt dit qui corrige la source, et comment.

Un test en avertissement ne bloque pas la chaîne : il signale des lignes à
corriger dans une source. Pour que la page « Qualité des données » puisse
les montrer au bon service, chacun doit avoir :
- store_failures : ses lignes en erreur sont gardées dans qualite_donnees ;
- meta.service : le service qui corrige ;
- meta.correction : ce qu'il faut corriger, et où.
Un nouvel avertissement ajouté sans ces trois informations est refusé ici.
"""

from pathlib import Path

import pytest
import yaml

DOSSIER_DBT = Path(__file__).resolve().parents[1] / "dbt"
IGNORES = {"dbt_packages", "target", "logs"}


def _fichiers(motif: str) -> list[Path]:
    return sorted(f for f in DOSSIER_DBT.rglob(motif) if not IGNORES & set(f.parts))


def _configs_en_avertissement(objet, chemin=""):
    """Blocs « config » d'un YAML dbt dont la sévérité est warn."""
    if isinstance(objet, dict):
        config = objet.get("config")
        if isinstance(config, dict) and config.get("severity") == "warn":
            yield chemin, config
        for cle, valeur in objet.items():
            yield from _configs_en_avertissement(valeur, f"{chemin}/{cle}")
    elif isinstance(objet, list):
        for i, valeur in enumerate(objet):
            yield from _configs_en_avertissement(valeur, f"{chemin}[{i}]")


AVERTISSEMENTS_YAML = [
    pytest.param(config, id=f"{fichier.name}{chemin}")
    for fichier in _fichiers("*.yml")
    for chemin, config in _configs_en_avertissement(
        yaml.safe_load(fichier.read_text(encoding="utf-8"))
    )
]

AVERTISSEMENTS_SQL = [
    pytest.param(f.read_text(encoding="utf-8"), id=f.name)
    for f in _fichiers("tests/**/*.sql")
    if "severity='warn'" in f.read_text(encoding="utf-8")
]


def test_il_y_a_des_avertissements_a_verifier():
    assert len(AVERTISSEMENTS_YAML) >= 8
    assert len(AVERTISSEMENTS_SQL) >= 12


@pytest.mark.parametrize("config", AVERTISSEMENTS_YAML)
def test_avertissement_yaml_dit_qui_corrige(config):
    assert config.get("store_failures") is True
    meta = config.get("meta") or {}
    assert meta.get("service"), "meta.service manquant"
    assert meta.get("correction"), "meta.correction manquant"


@pytest.mark.parametrize("sql", AVERTISSEMENTS_SQL)
def test_avertissement_sql_dit_qui_corrige(sql):
    assert "store_failures=true" in sql
    assert "'service':" in sql
    assert "'correction':" in sql
