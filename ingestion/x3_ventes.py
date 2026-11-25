"""Copie des factures clientes de Sage X3 vers la couche raw de l'entrepôt.

Utilisation, depuis la racine du dépôt :

    # Afficher ce qui serait lu et écrit, sans rien lire ni écrire
    uv run python -m ingestion.x3_ventes --simulation

    # Copier, puis rapprocher la source et l'entrepôt
    uv run python -m ingestion.x3_ventes

Source : Sage X3, dossier BASE1, en lecture seule et sans verrou.
Destination : schéma raw_x3 de l'entrepôt (compte analytix_chargeur).

    BASE1.SINVOICE   entêtes de factures et d'avoirs → raw_x3.sinvoice
    BASE1.SINVOICED  lignes de factures et d'avoirs  → raw_x3.sinvoiced

Ces tables font moins de 100 000 lignes : elles sont recopiées en entier
à chaque passage (cahier des charges, 8.4 a). La copie est remplacée
d'un coup : un échec laisse la copie précédente en place.

La couche raw est une copie fidèle : aucune règle métier ici. Le signe
des avoirs, les dates 1753 ou les espaces seront traités dans staging.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime

from ingestion.colonnes import colonnes_a_copier
from ingestion.config import EntrepotChargeur, SourceX3, parametres, sources
from ingestion.sqlserver import (
    connecter,
    decision_compte,
    droits_interdits,
    moteur_sqlalchemy,
    sans_verrou,
    verifier_droits,
)

NOM_PIPELINE = "x3_ventes"
SCHEMA_RAW = "raw_x3"


@dataclass(frozen=True)
class TableX3:
    """Une table Sage X3 copiée dans raw_x3."""

    nom: str
    # Clé naturelle : identifie une ligne (contrôlée au rapprochement)
    cle: tuple[str, ...]
    # Colonne de montant additionnée au rapprochement
    montant: str
    # Colonnes jamais copiées
    exclues: frozenset[str] = field(default_factory=frozenset)
    # Colonnes repérées par le contrôle des données sensibles, vérifiées sans risque
    autorisees: frozenset[str] = field(default_factory=frozenset)

    @property
    def destination(self) -> str:
        return self.nom.lower()


TABLES = (
    TableX3(
        nom="SINVOICE",
        cle=("NUM_0",),
        montant="AMTATI_0",  # montant TTC de la facture
        exclues=frozenset({"PAYBAN_0"}),  # banque de paiement du client
    ),
    TableX3(
        nom="SINVOICED",
        cle=("NUM_0", "SIDLIN_0"),
        montant="AMTATILIN_0",  # montant TTC de la ligne
        # BPC INV = code du client facturé (pas un numéro de CIN)
        autorisees=frozenset({"BPCINV_0"}),
    ),
)


# ─── Lecture de la structure (métadonnées seulement) ─────────────────


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


def exiger_lecture_seule(source: SourceX3, curseur_connexion) -> None:
    """Refuse de lire si le compte peut écrire, sauf dérogation déclarée."""
    droits = verifier_droits(curseur_connexion, (source.dossier,))
    problemes = droits_interdits(droits)
    if decision_compte(problemes, source.compte_admin_accepte) == "refuse":
        raise PermissionError(
            f"compte « {droits['compte']} » refusé, il peut modifier Sage X3 : {problemes}"
        )


# ─── Copie ───────────────────────────────────────────────────────────


def charger(simulation: bool = False) -> dict[str, list[str]]:
    """Copie les tables de TABLES. Retourne les colonnes copiées par table."""
    params = parametres()
    source = sources()["x3"]
    assert isinstance(source, SourceX3)
    if not source.configuree:
        raise SystemExit("Sage X3 non configuré dans .env (X3_HOST…)")

    # 1. Contrôles, avant de lire la moindre donnée
    with connecter(source, params) as connexion:
        exiger_lecture_seule(source, connexion)
        curseur = connexion.cursor()
        plan = {
            table.nom: colonnes_a_copier(
                colonnes_source(curseur, source.dossier, table.nom),
                table.exclues,
                table.autorisees,
            )
            for table in TABLES
        }

    for table in TABLES:
        colonnes = plan[table.nom]
        print(
            f"{source.dossier}.{table.nom} → {SCHEMA_RAW}.{table.destination} : "
            f"{len(colonnes)} colonnes copiées"
            + (f", exclues : {sorted(table.exclues)}" if table.exclues else "")
        )
    if simulation:
        print("\nSimulation : rien n'a été lu ni écrit.")
        return plan

    # 2. Copie avec dlt
    import dlt
    from dlt.sources.sql_database import sql_table

    entrepot = EntrepotChargeur()
    moteur = moteur_sqlalchemy(source, params)
    charge_le = datetime.now(UTC)

    def ajouter_tracabilite(nom_table: str):
        origine = f"x3.{source.dossier}.{nom_table}"

        def ajouter(ligne: dict) -> dict:
            ligne["_source"] = origine
            ligne["_charge_le"] = charge_le
            return ligne

        return ajouter

    ressources = [
        sql_table(
            credentials=moteur,
            schema=source.dossier,
            table=table.nom,
            included_columns=plan[table.nom],
            reflection_level="full_with_precision",  # garde la précision des montants
            backend="sqlalchemy",
            chunk_size=10_000,
            query_adapter_callback=sans_verrou,  # SELECT … WITH (NOLOCK)
        )
        .with_name(table.destination)
        .add_map(ajouter_tracabilite(table.nom))
        for table in TABLES
    ]
    for ressource in ressources:
        ressource.apply_hints(write_disposition="replace")

    pipeline = dlt.pipeline(
        pipeline_name=NOM_PIPELINE,
        destination=dlt.destinations.postgres(credentials=entrepot.identifiants_dlt()),
        dataset_name=SCHEMA_RAW,
    )
    info = pipeline.run(ressources)
    print(f"\n{info}")
    return plan


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    options = parseur.parse_args(arguments)
    charger(simulation=options.simulation)
    if options.simulation:
        return 0

    from ingestion.rapprochement import rapprocher_x3_ventes

    return 0 if rapprocher_x3_ventes() else 1


if __name__ == "__main__":
    sys.exit(main())
