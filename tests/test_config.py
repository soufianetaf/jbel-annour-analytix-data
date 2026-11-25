"""Tests de la lecture de la configuration (ingestion/config.py)."""

import pytest
from pydantic import ValidationError

from ingestion.config import Parametres, SourceUsine, SourceX3


def test_source_lue_avec_son_prefixe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X3_HOST", "serveur\\INSTANCE")
    monkeypatch.setenv("X3_USER", "lecteur")
    monkeypatch.setenv("X3_PASSWORD", "secret")
    # La variable d'une autre source ne doit pas être prise
    monkeypatch.setenv("USINE_HOST", "autre-serveur")

    source = SourceX3(_env_file=None)

    assert source.host == "serveur\\INSTANCE"
    assert source.user == "lecteur"
    assert source.dossier == "BASE1"


def test_mot_de_passe_jamais_affiche(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X3_HOST", "serveur")
    monkeypatch.setenv("X3_USER", "lecteur")
    monkeypatch.setenv("X3_PASSWORD", "MotDePasse123")

    source = SourceX3(_env_file=None)

    assert "MotDePasse123" not in repr(source)
    assert "MotDePasse123" not in str(source)
    assert source.password is not None
    assert source.password.get_secret_value() == "MotDePasse123"


def test_source_vide_est_non_configuree() -> None:
    source = SourceUsine(_env_file=None)

    assert not source.configuree


def test_valeur_vide_vaut_non_renseignee(monkeypatch: pytest.MonkeyPatch) -> None:
    # Dans .env.example, les ports sont laissés vides : « USINE_PORT= »
    monkeypatch.setenv("USINE_HOST", "serveur")
    monkeypatch.setenv("USINE_PORT", "")
    monkeypatch.setenv("USINE_AUTH", "windows")

    source = SourceUsine(_env_file=None)

    assert source.port is None


def test_authentification_sql_sans_mot_de_passe_refusee(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X3_HOST", "serveur")
    monkeypatch.setenv("X3_USER", "lecteur")

    with pytest.raises(ValidationError, match="mot de passe"):
        SourceX3(_env_file=None)


def test_authentification_windows_sans_mot_de_passe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USINE_HOST", "serveur")
    monkeypatch.setenv("USINE_AUTH", "windows")

    source = SourceUsine(_env_file=None)

    assert source.configuree
    assert source.password is None


def test_parametres_par_defaut() -> None:
    params = Parametres(_env_file=None)

    assert params.analytix_env == "dev"
    assert params.odbc_driver == "ODBC Driver 18 for SQL Server"
    assert params.sqlserver_trust_cert is False


def test_environnement_inconnu_refuse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANALYTIX_ENV", "production")

    with pytest.raises(ValidationError):
        Parametres(_env_file=None)


def test_exception_compte_admin_desactivee_par_defaut(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USINE_HOST", "serveur")
    monkeypatch.setenv("USINE_AUTH", "windows")

    assert SourceUsine(_env_file=None).compte_admin_accepte is False


def test_exception_compte_admin_propre_a_chaque_source(monkeypatch: pytest.MonkeyPatch) -> None:
    # L'exception de l'usine ne s'applique pas à Sage X3
    monkeypatch.setenv("USINE_COMPTE_ADMIN_ACCEPTE", "yes")

    assert SourceUsine(_env_file=None).compte_admin_accepte is True
    assert SourceX3(_env_file=None).compte_admin_accepte is False
