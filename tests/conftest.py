"""Isolation des tests : ils ne lisent jamais le vrai fichier .env."""

import os

import pytest

PREFIXES = ("X3_", "JBELRH_", "USINE_", "ANALYTIX_", "ODBC_", "SQLSERVER_")


@pytest.fixture(autouse=True)
def environnement_vide(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retire du test les variables d'environnement du projet.

    Chaque test construit sa configuration lui-même ; le vrai .env est
    désactivé par ``_env_file=None`` dans les tests de configuration.
    """
    for nom in list(os.environ):
        if nom.upper().startswith(PREFIXES):
            monkeypatch.delenv(nom)
