"""Moteur commun de copie Sage X3 → couche raw de l'entrepôt.

Chaque département a son petit module (``x3_ventes``, ``x3_finance``…)
qui décrit SES tables avec ``TableX3`` et appelle ``executer``. Toute la
mécanique est ici, une seule fois :

1. Contrôles avant de lire la moindre donnée : compte en lecture seule
   (ou dérogation déclarée), structure de chaque table, colonnes sensibles.
2. Copie avec dlt, en lecture seule, ``WITH (NOLOCK)``, par blocs.
3. Traçabilité : colonnes ``_source`` et ``_charge_le`` sur chaque ligne.

Deux façons de copier une table (cahier des charges, 8.4 a) :

- **complète** (par défaut) : la table est recopiée en entier et remplace
  l'ancienne copie d'un coup. Pour les tables de moins de 100 000 lignes ;
- **incrémentale** (``incremental=…``) : seules les lignes modifiées depuis
  la dernière copie sont lues, plus ``lag_jours`` jours par sécurité, et
  fusionnées par clé. Pour les grosses tables modifiables. Une copie
  complète (``--complet``) est à lancer chaque semaine : elle rattrape les
  modifications qui auraient échappé à la date de modification, et retire
  les lignes supprimées dans la source.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import UTC, datetime

from ingestion.colonnes import colonnes_a_copier
from ingestion.config import EntrepotChargeur, SourceSqlServer, SourceX3, parametres, sources
from ingestion.sqlserver import (
    connecter,
    decision_compte,
    droits_interdits,
    moteur_sqlalchemy,
    sans_verrou,
    verifier_droits,
)

SCHEMA_RAW = "raw_x3"
SECONDES_PAR_JOUR = 86_400


@dataclass(frozen=True)
class TableX3:
    """Une table Sage X3 copiée dans raw_x3."""

    nom: str
    # Clé naturelle : identifie une ligne (fusion incrémentale, contrôle des doublons)
    cle: tuple[str, ...]
    # Colonne de montant additionnée au rapprochement (aucune pour un référentiel)
    montant: str | None = None
    # Colonnes jamais copiées
    exclues: frozenset[str] = field(default_factory=frozenset)
    # Colonnes repérées par le contrôle des données sensibles, vérifiées sans risque
    autorisees: frozenset[str] = field(default_factory=frozenset)
    # Liste fermée : si elle est donnée, seules ces colonnes sont copiées
    seulement: tuple[str, ...] | None = None
    # Copie incrémentale : colonne de date de modification (ex. UPDDATTIM_0)
    incremental: str | None = None
    # Jours relus à chaque passage, par sécurité (modifications tardives)
    lag_jours: int = 3

    @property
    def destination(self) -> str:
        return self.nom.lower()


@dataclass(frozen=True)
class Cible:
    """Où lire (source, base, schéma SQL Server) et où écrire (schéma raw).

    Sage X3 : la base est celle du .env, le schéma est le dossier (BASE1).
    Serveur de l'usine : une base par application (Magasin…), schéma dbo,
    et un schéma raw par base (raw_magasin…), comme le prévoit le cahier
    des charges (8.2).
    """

    source: str = "x3"
    base: str | None = None
    schema_source: str | None = None  # None : dossier X3 du .env
    schema_raw: str = SCHEMA_RAW

    def schema_lu(self, source: SourceSqlServer) -> str:
        if self.schema_source:
            return self.schema_source
        assert isinstance(source, SourceX3), "schéma source obligatoire hors Sage X3"
        return source.dossier

    def origine(self, source: SourceSqlServer, table: str) -> str:
        base = f"{self.base}." if self.base else ""
        return f"{self.source}.{base}{self.schema_lu(source)}.{table}"


CIBLE_X3 = Cible()


# ─── Contrôles (métadonnées seulement) ───────────────────────────────


def colonnes_source(curseur, dossier: str, table: str) -> list[str]:
    """Colonnes d'une table X3, lues dans INFORMATION_SCHEMA (aucune donnée)."""
    curseur.execute(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
        dossier,
        table,
    )
    colonnes = [ligne[0] for ligne in curseur.fetchall()]
    if not colonnes:
        raise LookupError(f"table {dossier}.{table} introuvable")
    return colonnes


def exiger_lecture_seule(source: SourceSqlServer, connexion, schemas: tuple[str, ...]) -> None:
    """Refuse de lire si le compte peut écrire, sauf dérogation déclarée.

    Avec une dérogation (compte « sa » de l'usine), la lecture est permise
    et un avertissement est affiché : seules des lectures sont faites.
    """
    droits = verifier_droits(connexion, schemas)
    problemes = droits_interdits(droits)
    decision = decision_compte(problemes, source.compte_admin_accepte)
    if decision == "refuse":
        raise PermissionError(
            f"compte « {droits['compte']} » refusé, il peut modifier la source : {problemes}"
        )
    if decision == "tolere":
        print(
            f"ATTENTION : compte « {droits['compte']} » toléré par dérogation "
            "(il peut écrire) ; Analytix n'exécute que des lectures.\n"
        )


def verifier_tables(tables: tuple[TableX3, ...], colonnes_par_table: dict[str, list[str]]):
    """Colonnes à copier pour chaque table, après tous les contrôles."""
    plan = {}
    for table in tables:
        colonnes = colonnes_par_table[table.nom]
        copiees = colonnes_a_copier(colonnes, table.exclues, table.autorisees, table.seulement)
        manquantes = [c for c in (*table.cle, table.incremental) if c and c not in copiees]
        if manquantes:
            raise ValueError(f"{table.nom} : clé ou date de modification non copiée {manquantes}")
        plan[table.nom] = copiees
    return plan


# ─── Copie ───────────────────────────────────────────────────────────


def charger(
    nom_pipeline: str,
    tables: tuple[TableX3, ...],
    simulation: bool = False,
    complet: bool = False,
    cible: Cible = CIBLE_X3,
) -> dict[str, list[str]]:
    """Copie ``tables`` de la source décrite par ``cible`` dans son schéma raw.

    Retourne les colonnes copiées par table.
    ``complet`` : recopie entièrement aussi les tables incrémentales.
    """
    params = parametres()
    source = sources()[cible.source]
    if not source.configuree:
        raise SystemExit(f"source « {cible.source} » non configurée dans .env")
    schema = cible.schema_lu(source)

    # 1. Contrôles, avant de lire la moindre donnée
    with connecter(source, params, database=cible.base) as connexion:
        exiger_lecture_seule(source, connexion, (schema,))
        curseur = connexion.cursor()
        plan = verifier_tables(
            tables, {t.nom: colonnes_source(curseur, schema, t.nom) for t in tables}
        )

    for table in tables:
        if table.incremental and not complet:
            mode = f"incrémental sur {table.incremental}, reprise de {table.lag_jours} j"
        else:
            mode = "copie complète"
        print(
            f"{cible.origine(source, table.nom)} → {cible.schema_raw}.{table.destination} : "
            f"{len(plan[table.nom])} colonnes"
            + (" (liste fermée)" if table.seulement else "")
            + (f", exclues {sorted(table.exclues)}" if table.exclues else "")
            + f", {mode}"
        )
    if simulation:
        print("\nSimulation : rien n'a été lu ni écrit.")
        return plan

    # 2. Copie avec dlt
    import dlt
    from dlt.sources.sql_database import sql_table

    moteur = moteur_sqlalchemy(source, params, database=cible.base)
    charge_le = datetime.now(UTC)

    def tracabilite(nom_table: str):
        origine = cible.origine(source, nom_table)

        def ajouter(ligne: dict) -> dict:
            ligne["_source"] = origine
            ligne["_charge_le"] = charge_le
            return ligne

        return ajouter

    ressources = []
    for table in tables:
        incrementale = table.incremental is not None and not complet
        ressource = sql_table(
            credentials=moteur,
            schema=schema,
            table=table.nom,
            included_columns=plan[table.nom],
            reflection_level="full_with_precision",  # garde la précision des montants
            backend="sqlalchemy",
            chunk_size=10_000,
            query_adapter_callback=sans_verrou,  # SELECT … WITH (NOLOCK)
            incremental=(
                dlt.sources.incremental(table.incremental, lag=table.lag_jours * SECONDES_PAR_JOUR)
                if incrementale
                else None
            ),
        )
        ressource = ressource.with_name(table.destination).add_map(tracabilite(table.nom))
        if incrementale:
            ressource.apply_hints(
                write_disposition={"disposition": "merge", "strategy": "delete-insert"},
                primary_key=list(table.cle),
            )
        else:
            ressource.apply_hints(write_disposition="replace", primary_key=list(table.cle))
        ressources.append(ressource)

    pipeline = dlt.pipeline(
        pipeline_name=nom_pipeline,
        destination=dlt.destinations.postgres(credentials=EntrepotChargeur().identifiants_dlt()),
        dataset_name=cible.schema_raw,
    )
    print(f"\n{pipeline.run(ressources)}")
    return plan


def executer(
    nom_pipeline: str,
    tables: tuple[TableX3, ...],
    description: str,
    arguments: list[str] | None = None,
    cible: Cible = CIBLE_X3,
) -> int:
    """Ligne de commande commune : --simulation, --complet, puis rapprochement."""
    parseur = argparse.ArgumentParser(description=description)
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    parseur.add_argument(
        "--complet", action="store_true", help="recopie entière, y compris des tables incrémentales"
    )
    options = parseur.parse_args(arguments)
    charger(
        nom_pipeline, tables, simulation=options.simulation, complet=options.complet, cible=cible
    )
    if options.simulation:
        return 0

    from ingestion.rapprochement import rapprocher_tables

    return 0 if rapprocher_tables(tables, cible) else 1
