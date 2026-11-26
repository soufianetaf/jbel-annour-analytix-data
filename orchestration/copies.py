"""Les copies des sources (modules ingestion.*), vues par Dagster.

Chaque module d'ingestion devient un actif Dagster qui produit SES tables
brutes, sous le nom exact de la table dans l'entrepôt (raw_x3.sinvoice,
raw_rh.effectifs_service…). dbt lit ces mêmes tables comme sources :
Dagster relie donc chaque copie aux modèles qui en dépendent.

Une copie qui échoue, ou dont le rapprochement avec la source trouve un
écart (le module rend un code différent de 0), fait échouer l'actif : les
modèles dbt qui en dépendent ne sont pas reconstruits avec des données fausses.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from dataclasses import dataclass
from types import ModuleType

from dagster import AssetKey, AssetSpec, Failure, MaterializeResult, multi_asset

# Ordre de lancement : Sage X3 d'abord, puis le serveur de l'usine
MODULES_COPIE = (
    "x3_ventes",
    "x3_finance",
    "x3_stock",
    "x3_achats",
    "usine_magasin",
    "usine_production",
    "usine_machines",
    "usine_electricite",
    "usine_qualite",
    "usine_maintenance",
    "usine_rh",
)


@dataclass(frozen=True)
class Copie:
    nom: str
    module: ModuleType
    tables: tuple[AssetKey, ...]  # [schéma raw, table]


def tables_brutes(module: ModuleType) -> tuple[AssetKey, ...]:
    """Tables que le module écrit dans l'entrepôt, sous la forme [schéma raw, table]."""
    from ingestion.x3 import CIBLE_X3

    if hasattr(module, "AGREGATS"):  # usine_rh : agrégats, pas des tables copiées
        return tuple(AssetKey([module.SCHEMA_RAW, a.nom]) for a in module.AGREGATS)
    if hasattr(module, "COPIES"):  # plusieurs bases ou schémas sources
        groupes = [(cible, tables) for _, tables, cible in module.COPIES]
    else:
        cibles = [v for v in vars(module).values() if type(v).__name__ == "Cible"]
        groupes = [(cibles[0] if cibles else CIBLE_X3, module.TABLES)]
    return tuple(
        AssetKey([cible.schema_raw, table.destination])
        for cible, tables in groupes
        for table in tables
    )


def copies() -> list[Copie]:
    resultat = []
    for nom in MODULES_COPIE:
        module = importlib.import_module(f"ingestion.{nom}")
        resultat.append(Copie(nom, module, tables_brutes(module)))
    return resultat


def actif_copie(copie: Copie):
    """Un actif Dagster qui lance le module d'ingestion et produit ses tables brutes."""

    @multi_asset(
        name=f"copie_{copie.nom}",
        specs=[
            AssetSpec(cle, group_name="copies", kinds={"python", "sqlserver"})
            for cle in copie.tables
        ],
        description=(copie.module.__doc__ or "").splitlines()[0],
    )
    def _copie(context) -> Iterator[MaterializeResult]:
        context.log.info(f"Copie ingestion.{copie.nom} : {len(copie.tables)} tables")
        try:
            code = copie.module.main([])
        except SystemExit as arret:  # un module qui s'arrête avec un message
            raise Failure(f"ingestion.{copie.nom} arrêtée : {arret}") from arret
        if code:
            raise Failure(
                f"ingestion.{copie.nom} : rapprochement en écart avec la source (code {code}). "
                "Les modèles dbt qui en dépendent ne seront pas reconstruits."
            )
        for cle in copie.tables:
            yield MaterializeResult(asset_key=cle)

    return _copie
