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
    assert {"staging", "intermediate", "marts", "snapshots", "quality", "api"} <= schemas


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


def test_api_lit_les_comptes(api) -> None:
    # La connexion des utilisateurs relit leur compte à chaque requête
    api.execute("SELECT count(*) FROM api.utilisateurs")
    assert api.fetchone()[0] >= 0


def test_api_ne_peut_pas_modifier_les_comptes(api) -> None:
    # Personne ne se donne un rôle par l'API : même hors lecture seule, refusé
    api.execute("SET default_transaction_read_only = off")
    with pytest.raises(errors.InsufficientPrivilege):
        api.execute(
            "INSERT INTO api.utilisateurs (identifiant, empreinte_mot_de_passe, role) "
            "VALUES ('intrus', 'x', 'direction')"
        )
    with pytest.raises(errors.InsufficientPrivilege):
        api.execute("UPDATE api.utilisateurs SET role = 'direction'")


def test_groupe_de_lecture_ne_voit_pas_les_comptes(entrepot: ConfigEntrepot) -> None:
    # Power BI passera par le groupe de lecture de marts : jamais les empreintes
    with (
        closing(_connexion(entrepot, entrepot.dw_user, entrepot.dw_password)) as connexion,
        connexion.cursor() as curseur,
    ):
        curseur.execute(
            "SELECT has_table_privilege('analytix_lecture_marts', 'api.utilisateurs', 'SELECT')"
        )
        assert curseur.fetchone()[0] is False


# ─── Sécurité par ligne (macro dbt securite_par_ligne) ───────────────


def _politique_dbt(table: str, role_api: str) -> list[str]:
    """Les instructions de la macro dbt, telles quelles, pour une table d'essai.

    Le test lit le fichier de la macro : il vérifie la vraie règle, pas une copie.
    """
    import re
    from pathlib import Path

    texte = (
        Path(__file__).resolve().parents[1] / "dbt" / "macros" / "securite_par_ligne.sql"
    ).read_text(encoding="utf-8")
    corps = re.search(r"-%\}(.*?)\{%-\s*endmacro", texte, re.S).group(1)
    corps = corps.replace("{{ this }}", table).replace("{{ colonne }}", "representant")
    corps = corps.replace("""{{ var("role_api") }}""", role_api)
    return [instruction.strip() for instruction in corps.split(";") if instruction.strip()]


@pytest.fixture
def table_protegee(entrepot: ConfigEntrepot):
    with (
        closing(_connexion(entrepot, entrepot.dw_user, entrepot.dw_password)) as chargeur,
        chargeur.cursor() as curseur,
    ):
        curseur.execute("DROP TABLE IF EXISTS marts.essai_rls")
        curseur.execute("CREATE TABLE marts.essai_rls (representant text, montant int)")
        curseur.execute(
            "INSERT INTO marts.essai_rls VALUES ('R1', 10), ('R1', 20), ('R2', 5), (NULL, 1)"
        )
        for instruction in _politique_dbt("marts.essai_rls", entrepot.api_db_user):
            curseur.execute(instruction)
    yield "marts.essai_rls"
    with (
        closing(_connexion(entrepot, entrepot.dw_user, entrepot.dw_password)) as chargeur,
        chargeur.cursor() as curseur,
    ):
        curseur.execute("DROP TABLE IF EXISTS marts.essai_rls")


def _lignes_vues(api, table: str, perimetre: str | None) -> int:
    api.execute("BEGIN")
    if perimetre is not None:
        api.execute("SELECT set_config('analytix.perimetre', %s, true)", (perimetre,))
    api.execute(f"SELECT count(*) FROM {table}")  # noqa: S608 - nom de table du test
    vues = api.fetchone()[0]
    api.execute("COMMIT")
    return vues


@pytest.mark.parametrize(
    ("perimetre", "attendu"),
    [
        (None, 0),  # périmètre oublié : rien, jamais tout
        ("", 0),
        ("R9", 0),  # code inconnu
        ("R1", 2),  # ses lignes seulement
        ("*", 4),  # direction, commercial : tout
    ],
)
def test_securite_par_ligne_pour_l_api(api, table_protegee, perimetre, attendu) -> None:
    assert _lignes_vues(api, table_protegee, perimetre) == attendu


def test_le_perimetre_ne_survit_pas_a_la_transaction(api, table_protegee) -> None:
    # Une connexion réutilisée (pool) ne garde pas le périmètre du précédent
    assert _lignes_vues(api, table_protegee, "*") == 4
    assert _lignes_vues(api, table_protegee, None) == 0


def test_le_chargeur_voit_toutes_les_lignes(entrepot: ConfigEntrepot, table_protegee) -> None:
    # dbt (propriétaire des tables) n'est jamais filtré : les agrégats restent complets
    with (
        closing(_connexion(entrepot, entrepot.dw_user, entrepot.dw_password)) as chargeur,
        chargeur.cursor() as curseur,
    ):
        curseur.execute(f"SELECT count(*) FROM {table_protegee}")  # noqa: S608
        assert curseur.fetchone()[0] == 4
