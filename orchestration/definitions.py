"""Définitions Dagster : copies, modèles dbt, rapprochements, planification, alerte.

Toutes les deux heures (cahier des charges), dans l'ordre que Dagster
déduit des dépendances :
1. les copies des sources (une par module d'ingestion), chacune rapprochée
   de sa source ;
2. dbt build : modèles, tests, photos quotidiennes, historique de la
   qualité des données ;
3. les rapprochements métier (CA, créances, résultat, trésorerie, stock,
   achats) entre Sage X3 et les tables finales.

Tout tourne l'un après l'autre (exécuteur « in_process ») : les serveurs
sources sont en production, on ne les sollicite pas en parallèle.
La planification est créée ARRÊTÉE : on l'active dans l'interface quand
on le décide (docs/orchestration.md).
"""

from __future__ import annotations

import os
from pathlib import Path

from dagster import (
    AssetKey,
    AssetSelection,
    DagsterRunStatus,
    DefaultScheduleStatus,
    DefaultSensorStatus,
    Definitions,
    Failure,
    RunFailureSensorContext,
    RunRequest,
    RunsFilter,
    ScheduleEvaluationContext,
    SkipReason,
    asset,
    define_asset_job,
    in_process_executor,
    run_failure_sensor,
    schedule,
)
from dagster_dbt import (
    DagsterDbtTranslator,
    DbtCliResource,
    DbtProject,
    dbt_assets,
    get_asset_key_for_model,
)

from orchestration.copies import actif_copie, copies

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_DBT = RACINE / "dbt"
FUSEAU = "Africa/Casablanca"
FREQUENCE = "0 */2 * * *"  # toutes les deux heures, à l'heure pile

# dbt lit ses paramètres de connexion dans l'environnement (dbt/profiles.yml) :
# on charge le .env, sans écraser une variable déjà définie (serveur de prod)
try:
    from dotenv import load_dotenv

    load_dotenv(RACINE / ".env", override=False)
except ImportError:  # pragma: no cover - python-dotenv vient avec dlt
    pass
os.environ.setdefault("PYTHONIOENCODING", "utf-8")  # accents des journaux dbt sous Windows

projet_dbt = DbtProject(project_dir=DOSSIER_DBT, profiles_dir=DOSSIER_DBT)
projet_dbt.prepare_if_dev()  # « dagster dev » : relit le projet dbt (dbt parse)


class Traducteur(DagsterDbtTranslator):
    """Relie les sources dbt aux copies, et range les modèles par couche."""

    def get_asset_key(self, dbt_resource_props) -> AssetKey:
        # Une source dbt dans un schéma raw_… est la table produite par une copie
        if dbt_resource_props["resource_type"] == "source" and dbt_resource_props[
            "schema"
        ].startswith("raw_"):
            return AssetKey([dbt_resource_props["schema"], dbt_resource_props["name"]])
        return super().get_asset_key(dbt_resource_props)

    def get_group_name(self, dbt_resource_props) -> str | None:
        # staging, intermediate, marts, snapshots : le dossier du modèle
        fqn = dbt_resource_props.get("fqn") or []
        return fqn[1] if len(fqn) > 2 else "dbt"


@dbt_assets(manifest=projet_dbt.manifest_path, dagster_dbt_translator=Traducteur())
def modeles_dbt(context, dbt: DbtCliResource):
    """dbt build : modèles, tests et photos, dans l'ordre des dépendances."""
    yield from dbt.cli(["build"], context=context).stream()


TABLES_RAPPROCHEES = (
    "fct_ventes",
    "fct_echeances",
    "agg_compte_de_resultat_mois",
    "agg_tresorerie_jour",
    "fct_stock_article",
    "fct_achats_factures",
)


@asset(
    group_name="controles",
    kinds={"python"},
    deps=[get_asset_key_for_model([modeles_dbt], nom) for nom in TABLES_RAPPROCHEES],
)
def rapprochements_metier(context) -> None:
    """CA, créances, résultat, trésorerie, stock et achats : Sage X3 contre les tables finales."""
    from ingestion import rapprochement

    code = rapprochement.main([])
    if code:
        raise Failure(
            "Un rapprochement métier est en écart avec Sage X3 : voir le journal de l'exécution."
        )


ACTIFS_COPIE = [actif_copie(copie) for copie in copies()]

chargement_complet = define_asset_job(
    "chargement_complet",
    selection=AssetSelection.all(),
    executor_def=in_process_executor,
    description="Copies des sources, dbt build, rapprochements métier.",
)


@schedule(
    job=chargement_complet,
    cron_schedule=FREQUENCE,
    execution_timezone=FUSEAU,
    default_status=DefaultScheduleStatus.STOPPED,
)
def toutes_les_deux_heures(context: ScheduleEvaluationContext):
    """Lance le chargement, sauf si le précédent tourne encore (jamais deux à la fois)."""
    en_cours = context.instance.get_runs(
        filters=RunsFilter(
            job_name=chargement_complet.name,
            statuses=[DagsterRunStatus.QUEUED, DagsterRunStatus.STARTING, DagsterRunStatus.STARTED],
        ),
        limit=1,
    )
    if en_cours:
        return SkipReason("Le chargement précédent tourne encore : celui-ci est sauté.")
    return RunRequest()


@run_failure_sensor(
    monitored_jobs=[chargement_complet],
    default_status=DefaultSensorStatus.RUNNING,
)
def alerte_echec(context: RunFailureSensorContext) -> None:
    """Un chargement en échec est signalé dans le journal de Dagster.

    L'envoi d'un courriel au responsable viendra quand le serveur de
    messagerie sera connu (docs/orchestration.md, points à valider).
    """
    context.log.error(
        f"Chargement en échec ({context.dagster_run.run_id}) : "
        f"{context.failure_event.message}. Les chiffres de l'API ne sont pas à jour."
    )


defs = Definitions(
    assets=[*ACTIFS_COPIE, modeles_dbt, rapprochements_metier],
    jobs=[chargement_complet],
    schedules=[toutes_les_deux_heures],
    sensors=[alerte_echec],
    resources={"dbt": DbtCliResource(project_dir=projet_dbt)},
)
