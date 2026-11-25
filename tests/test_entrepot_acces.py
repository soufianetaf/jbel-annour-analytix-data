"""Tests d'accès sur un vrai PostgreSQL : chaque compte a les droits prévus, pas plus.

Ces tests créent des tables : ils ne tournent que sur une base de test
**dw_test**, jamais sur dw_dev ni dw_prod. Ils sont ignorés sauf si
ANALYTIX_TEST_ENTREPOT=1 (la CI les lance sur un PostgreSQL jetable).

En local :

    $env:ANALYTIX_TEST_ENTREPOT='1'; $env:DW_DATABASE='dw_test'; uv run pytest -m entrepot
"""

import os
from contextlib import closing

import pytest

from infra.postgres.initialiser_entrepot import ConfigEntrepot, executer

pytestmark = [
    pytest.mark.entrepot,
    pytest.mark.skipif(
        os.environ.get("ANALYTIX_TEST_ENTREPOT") != "1",
        reason="PostgreSQL de test non demandé (ANALYTIX_TEST_ENTREPOT=1)",
    ),
]

psycopg2 = pytest.importorskip("psycopg2")
from psycopg2 import errors  # noqa: E402


@pytest.fixture(scope="module")
def config() -> ConfigEntrepot:
    # Lit DW_… et API_DB_… dans l'environnement du test (pas dans .env)
    config = ConfigEntrepot(_env_file=None)
    assert config.dw_database == "dw_test", "ces tests ne tournent que sur dw_test"
    return config


@pytest.fixture(scope="module")
def entrepot(config: ConfigEntrepot) -> ConfigEntrepot:
    # Deux passages : le second vérifie que le script est rejouable
    executer(config, simulation=False)
    executer(config, simulation=False)

    with (
        closing(_connexion(config, config.dw_user, config.dw_password)) as chargeur,
        chargeur.cursor() as curseur,
    ):
        curseur.execute("DROP TABLE IF EXISTS marts.essai_acces, staging.essai_acces")
        # Tables créées APRÈS l'initialisation, comme le fera dbt
        curseur.execute("CREATE TABLE marts.essai_acces (id int)")
        curseur.execute("INSERT INTO marts.essai_acces VALUES (1)")
        curseur.execute("CREATE TABLE staging.essai_acces (id int)")
    yield config
    with (
        closing(_connexion(config, config.dw_user, config.dw_password)) as chargeur,
        chargeur.cursor() as curseur,
    ):
        curseur.execute("DROP TABLE IF EXISTS marts.essai_acces, staging.essai_acces")


def _connexion(config: ConfigEntrepot, utilisateur: str, mot_de_passe):
    connexion = psycopg2.connect(
        host=config.dw_host,
        port=config.dw_port,
        dbname=config.dw_database,
        user=utilisateur,
        password=mot_de_passe.get_secret_value(),
    )
    connexion.autocommit = True
    return connexion


@pytest.fixture
def api(entrepot: ConfigEntrepot):
    connexion = _connexion(entrepot, entrepot.api_db_user, entrepot.api_db_password)
    yield connexion.cursor()
    connexion.close()


def test_schemas_crees(entrepot: ConfigEntrepot) -> None:
    with (
        closing(_connexion(entrepot, entrepot.dw_user, entrepot.dw_password)) as connexion,
        connexion.cursor() as curseur,
    ):
        curseur.execute("SELECT schema_name FROM information_schema.schemata")
        schemas = {ligne[0] for ligne in curseur.fetchall()}
    assert {"staging", "intermediate", "marts", "snapshots", "quality"} <= schemas


def test_chargeur_peut_creer_un_schema_raw(entrepot: ConfigEntrepot) -> None:
    # L'ingestion crée elle-même ses schémas raw_<source>
    with (
        closing(_connexion(entrepot, entrepot.dw_user, entrepot.dw_password)) as connexion,
        connexion.cursor() as curseur,
    ):
        curseur.execute("CREATE SCHEMA IF NOT EXISTS raw_essai")
        curseur.execute("DROP SCHEMA raw_essai")


def test_api_lit_les_tables_de_marts(api) -> None:
    # Y compris une table créée après l'initialisation (droits par défaut)
    api.execute("SELECT id FROM marts.essai_acces")
    assert api.fetchall() == [(1,)]


def test_api_ne_peut_pas_ecrire_dans_marts(api) -> None:
    with pytest.raises(errors.ReadOnlySqlTransaction):
        api.execute("INSERT INTO marts.essai_acces VALUES (2)")


def test_api_ne_peut_pas_creer_de_table(api) -> None:
    with pytest.raises((errors.ReadOnlySqlTransaction, errors.InsufficientPrivilege)):
        api.execute("CREATE TABLE marts.intrusion (id int)")


def test_api_ne_peut_pas_lire_staging(api) -> None:
    # Les données non nettoyées ne sortent jamais par l'API
    with pytest.raises(errors.InsufficientPrivilege):
        api.execute("SELECT * FROM staging.essai_acces")


def test_api_meme_hors_lecture_seule_ne_peut_pas_ecrire(api) -> None:
    # Si quelqu'un désactivait la lecture seule dans sa session, les droits
    # bloquent quand même l'écriture : deux protections indépendantes
    api.execute("SET default_transaction_read_only = off")
    with pytest.raises(errors.InsufficientPrivilege):
        api.execute("INSERT INTO marts.essai_acces VALUES (3)")
