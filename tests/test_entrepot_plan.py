"""Tests du plan d'initialisation de l'entrepôt, sans serveur PostgreSQL."""

import pytest
from pydantic import ValidationError

from infra.postgres.initialiser_entrepot import (
    GROUPE_LECTURE_MARTS,
    SCHEMAS,
    ConfigEntrepot,
    construire_plan,
)


def _config(**valeurs: str) -> ConfigEntrepot:
    base = {"dw_password": "mdp-chargeur", "api_db_password": "mdp-api"}
    return ConfigEntrepot(_env_file=None, **(base | valeurs))


def _sql(instructions) -> str:
    return "\n".join(instruction.sql for instruction in instructions)


# ─── Garde-fous de la configuration ─────────────────────────────────


@pytest.mark.parametrize("base", ["dw_dev", "dw_prod", "dw_test"])
def test_bases_de_l_entrepot_acceptees(base: str) -> None:
    assert _config(dw_database=base).dw_database == base


@pytest.mark.parametrize("base", ["dw_ventes", "postgres", "agent_ai", "dw_dev; DROP"])
def test_autres_bases_du_serveur_refusees(base: str) -> None:
    # Le serveur héberge d'autres projets : le script ne doit jamais les toucher
    with pytest.raises(ValidationError, match="refusée"):
        _config(dw_database=base)


@pytest.mark.parametrize("role", ["postgres", "dw_ventes", "agent_ai", 'analytix_x"; DROP'])
def test_roles_hors_analytix_refuses(role: str) -> None:
    # Le script change le mot de passe des rôles qu'il gère : jamais ceux des autres
    with pytest.raises(ValidationError, match="refusé"):
        _config(dw_user=role)
    with pytest.raises(ValidationError, match="refusé"):
        _config(api_db_user=role)


# ─── Contenu du plan ────────────────────────────────────────────────


def test_premiere_installation_cree_tout() -> None:
    plan = construire_plan(_config(), roles_existants=set(), base_existe=False)
    sql = _sql(plan.serveur)

    assert 'CREATE ROLE "analytix_chargeur"' in sql
    assert 'CREATE ROLE "analytix_api"' in sql
    assert f'CREATE ROLE "{GROUPE_LECTURE_MARTS}" NOLOGIN' in sql
    assert 'CREATE DATABASE "dw_dev" OWNER "analytix_chargeur"' in sql


def test_relance_ne_recree_rien() -> None:
    # Idempotence : relancer le script met à jour au lieu de recréer
    existants = {"analytix_chargeur", "analytix_api", GROUPE_LECTURE_MARTS}
    plan = construire_plan(_config(), roles_existants=existants, base_existe=True)
    sql = _sql(plan.serveur)

    assert "CREATE ROLE" not in sql
    assert "CREATE DATABASE" not in sql
    assert 'ALTER ROLE "analytix_chargeur"' in sql
    assert 'ALTER DATABASE "dw_dev" OWNER TO "analytix_chargeur"' in sql


def test_aucun_role_n_est_administrateur() -> None:
    plan = construire_plan(_config(), roles_existants=set(), base_existe=False)

    for instruction in plan.serveur:
        if " WITH LOGIN " in instruction.sql:
            assert "NOSUPERUSER NOCREATEDB NOCREATEROLE" in instruction.sql


def test_api_en_lecture_seule_forcee_par_le_serveur() -> None:
    plan = construire_plan(_config(), roles_existants=set(), base_existe=False)
    sql = _sql(plan.serveur)

    assert 'ALTER ROLE "analytix_api" SET default_transaction_read_only = on' in sql
    assert 'ALTER ROLE "analytix_api" SET statement_timeout' in sql
    assert f'GRANT "{GROUPE_LECTURE_MARTS}" TO "analytix_api"' in sql


def test_personne_d_autre_ne_se_connecte_a_l_entrepot() -> None:
    plan = construire_plan(_config(), roles_existants=set(), base_existe=False)

    assert 'REVOKE ALL ON DATABASE "dw_dev" FROM PUBLIC' in _sql(plan.serveur)


def test_tous_les_schemas_crees_et_fermes_au_public() -> None:
    sql = _sql(construire_plan(_config(), set(), False).entrepot)

    for schema in SCHEMAS:
        assert f'CREATE SCHEMA IF NOT EXISTS "{schema}" AUTHORIZATION "analytix_chargeur"' in sql
        assert f'REVOKE ALL ON SCHEMA "{schema}" FROM PUBLIC' in sql


def test_groupe_de_lecture_limite_a_marts() -> None:
    plan = construire_plan(_config(), set(), False)
    droits = [i.sql for i in plan.entrepot if GROUPE_LECTURE_MARTS in i.sql]

    assert droits, "le groupe de lecture doit recevoir des droits"
    for sql in droits:
        assert '"marts"' in sql
        assert "SELECT" in sql or "USAGE" in sql
        # Les droits accordés : entre « GRANT » et « ON »
        droits_accordes = sql.split("GRANT", 1)[1].split(" ON ", 1)[0]
        assert droits_accordes.strip() in {"SELECT", "USAGE"}


def test_mots_de_passe_jamais_affiches() -> None:
    plan = construire_plan(_config(), set(), False)
    affichage = "\n".join(i.affichage() for i in plan.serveur + plan.entrepot)

    assert "mdp-chargeur" not in affichage
    assert "mdp-api" not in affichage
    assert "PASSWORD '********'" in affichage


def test_mots_de_passe_passes_en_parametre() -> None:
    # Jamais concaténés dans le SQL : le pilote les protège
    plan = construire_plan(_config(), set(), False)

    assert all("mdp-" not in instruction.sql for instruction in plan.serveur)
    secrets = [i.parametres for i in plan.serveur if i.secret]
    assert ("mdp-chargeur",) in secrets
    assert ("mdp-api",) in secrets
