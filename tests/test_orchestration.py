"""Orchestration Dagster : rien n'est oublié, rien ne tourne en double.

Ces tests chargent les définitions Dagster, qui lisent le projet dbt
compilé (dbt/target/manifest.json, produit par « dbt parse ») : la CI les
lance dans le job dbt, juste après dbt parse. Sans manifeste, ils sont ignorés.
"""

from __future__ import annotations

from pathlib import Path

import pytest

MANIFESTE = Path(__file__).resolve().parents[1] / "dbt" / "target" / "manifest.json"
pytestmark = pytest.mark.skipif(
    not MANIFESTE.exists(), reason="projet dbt non compilé (lancer dbt parse)"
)

# Modules d'ingestion qui ne sont pas des copies (outils communs)
OUTILS = {
    "__init__",
    "colonnes",
    "config",
    "rapprochement",
    "sqlserver",
    "verifier_connexions",
    "x3",
}


@pytest.fixture(scope="module")
def definitions():
    from orchestration import defs

    return defs


@pytest.fixture(scope="module")
def graphe(definitions):
    return definitions.resolve_asset_graph()


def test_chaque_module_de_copie_est_orchestre():
    from orchestration.copies import MODULES_COPIE

    dossier = Path(__file__).resolve().parents[1] / "ingestion"
    modules = {f.stem for f in dossier.glob("*.py")} - OUTILS
    assert set(MODULES_COPIE) == modules


def test_chaque_source_dbt_brute_a_sa_copie(graphe):
    """Une source dbt raw_… sans copie ne serait jamais rechargée : ses chiffres vieilliraient."""
    orphelines = [
        cle.to_user_string()
        for cle in graphe.get_all_asset_keys()
        if cle.path[0].startswith("raw_") and not graphe.get(cle).is_materializable
    ]
    assert orphelines == []


def test_les_rapprochements_suivent_dbt(graphe):
    from dagster import AssetKey

    parents = graphe.get(AssetKey(["rapprochements_metier"])).parent_keys
    assert len(parents) == 6
    assert all(graphe.get(cle).is_materializable for cle in parents)


def test_un_seul_job_sequentiel(definitions):
    job = definitions.resolve_job_def("chargement_complet")
    # Les serveurs sources sont en production : une copie à la fois
    assert job.executor_def.name == "in_process"


def test_planification_toutes_les_deux_heures_et_arretee(definitions):
    from dagster import DefaultScheduleStatus

    planif = definitions.resolve_schedule_def("toutes_les_deux_heures")
    assert planif.cron_schedule == "0 */2 * * *"
    assert planif.execution_timezone == "Africa/Casablanca"
    # Créée arrêtée : on l'active dans l'interface, quand on le décide
    assert planif.default_status == DefaultScheduleStatus.STOPPED


def test_planification_lance_un_chargement_si_rien_ne_tourne(definitions):
    from dagster import RunRequest, build_schedule_context, instance_for_test

    planif = definitions.resolve_schedule_def("toutes_les_deux_heures")
    with instance_for_test() as instance:
        resultat = planif(build_schedule_context(instance=instance))
    assert isinstance(resultat, RunRequest)


def test_planification_sautee_si_le_chargement_precedent_tourne(definitions):
    """Jamais deux chargements à la fois : le second écrirait dans les mêmes tables."""
    from dagster import (
        DagsterRun,
        DagsterRunStatus,
        SkipReason,
        build_schedule_context,
        instance_for_test,
    )

    planif = definitions.resolve_schedule_def("toutes_les_deux_heures")
    with instance_for_test() as instance:
        instance.add_run(
            DagsterRun(
                job_name="chargement_complet", run_id="en-cours", status=DagsterRunStatus.STARTED
            )
        )
        resultat = planif(build_schedule_context(instance=instance))
    assert isinstance(resultat, SkipReason)


def test_alerte_en_cas_d_echec(definitions):
    from dagster import DefaultSensorStatus

    capteur = definitions.resolve_sensor_def("alerte_echec")
    assert capteur.default_status == DefaultSensorStatus.RUNNING
