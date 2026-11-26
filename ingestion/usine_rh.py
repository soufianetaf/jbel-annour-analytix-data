"""Copie RH AGRÉGÉE (serveur de l'usine, bases RH et pointage) vers l'entrepôt.

Utilisation, depuis la racine du dépôt :

    uv run python -m ingestion.usine_rh --simulation
    uv run python -m ingestion.usine_rh

Règle d'or (cahier des charges) : aucune donnée RH individuelle dans
l'entrepôt. Contrairement aux autres copies, on ne copie donc PAS des
tables mais le résultat de requêtes d'agrégation exécutées sur le serveur
source : SQL Server compte et additionne par service (et par jour), et
aucune ligne de salarié ne quitte le serveur. Aucun nom, matricule,
identifiant, date de naissance, téléphone ni taux horaire n'est lu.

Petits groupes : un groupe de moins de SEUIL_PERSONNES personnes permettrait
de retrouver quelqu'un (« le seul salarié du juridique a pointé 4 h ») :
il est fusionné dans « autres (moins de 5 personnes) » avant d'être écrit,
et ses mesures sensibles (minutes sur site) sont vidées si le groupe fusionné
reste petit. Les totaux sont conservés : le rapprochement les compare.

Jamais lus : le dossier Sage X3 JBELRH (paie, primes, livre de paie, RIB),
qui demande l'accord écrit de la direction et des RH ; les bases pointage_1,
pointage_2 et wdms (installations presque vides, en double).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

SEUIL_PERSONNES = 5
GROUPE_MASQUE = "autres (moins de 5 personnes)"
SCHEMA_RAW = "raw_rh"


@dataclass(frozen=True)
class Agregat:
    """Une requête d'agrégation exécutée sur la source, copiée telle quelle.

    ``groupe`` : colonne fusionnée quand ``personnes`` < SEUIL_PERSONNES.
    ``sommes`` : mesures additives, re-sommées après la fusion.
    ``sensibles`` : mesures vidées si le groupe fusionné reste sous le seuil.
    """

    nom: str
    base: str
    requete: str
    groupe: str
    cles: tuple[str, ...]
    sommes: tuple[str, ...]
    sensibles: tuple[str, ...] = ()


# Service ou département écrit en majuscules, sans espaces autour ; vide → NON RENSEIGNÉ
def _libelle(colonne: str) -> str:
    return f"UPPER(COALESCE(NULLIF(LTRIM(RTRIM({colonne})), ''), N'NON RENSEIGNÉ'))"


AGREGATS = (
    # Effectif actuel par service (application RH) : salariés non supprimés
    # et sans date de sortie (la source met 1753 pour « pas de sortie »)
    Agregat(
        nom="effectifs_service",
        base="RH",
        requete=f"""
            SELECT {_libelle("service")} AS service,
                   COUNT(*) AS personnes,
                   SUM(CASE WHEN hire_date >= DATEADD(year, -1, CAST(GETDATE() AS date))
                            THEN 1 ELSE 0 END) AS embauches_12_mois
            FROM dbo.employees WITH (NOLOCK)
            WHERE deleted_at IS NULL
              AND (date_s IS NULL OR YEAR(date_s) <= 1900 OR date_s > CAST(GETDATE() AS date))
            GROUP BY {_libelle("service")}
        """,
        groupe="service",
        cles=("service",),
        sommes=("personnes", "embauches_12_mois"),
    ),
    # Embauches par année, pour toute l'entreprise
    Agregat(
        nom="embauches_annee",
        base="RH",
        requete="""
            SELECT CAST(YEAR(hire_date) AS nvarchar(4)) AS annee, COUNT(*) AS personnes
            FROM dbo.employees WITH (NOLOCK)
            WHERE deleted_at IS NULL AND hire_date IS NOT NULL
            GROUP BY YEAR(hire_date)
        """,
        groupe="annee",
        cles=("annee",),
        sommes=("personnes",),
    ),
    # Effectif enregistré dans les pointeuses, par département
    Agregat(
        nom="effectifs_pointeuse",
        base="pointage",
        requete=f"""
            SELECT {_libelle("d.dept_name")} AS service, COUNT(*) AS personnes
            FROM dbo.hr_employee AS e WITH (NOLOCK)
            LEFT JOIN dbo.hr_department AS d WITH (NOLOCK) ON d.id = e.department_id
            WHERE e.emp_active = 1
            GROUP BY {_libelle("d.dept_name")}
        """,
        groupe="service",
        cles=("service",),
        sommes=("personnes",),
    ),
    # Présence par département et par jour, d'après les pointages bruts :
    # une personne est présente si elle a pointé ; temps sur site = dernier
    # pointage - premier pointage du jour, quand il y en a au moins deux
    Agregat(
        nom="pointage_service_jour",
        base="pointage",
        # Sous-requête plutôt que WITH : la requête est aussi enveloppée par
        # totaux_source, et SQL Server refuse un WITH dans une sous-requête
        requete=f"""
            SELECT {_libelle("d.dept_name")} AS service,
                   CONVERT(char(10), j.jour, 23) AS jour,
                   COUNT(*) AS personnes,
                   SUM(j.pointages) AS pointages,
                   SUM(CASE WHEN j.pointages >= 2 THEN 1 ELSE 0 END) AS personnes_entree_sortie,
                   SUM(CASE WHEN j.pointages >= 2 THEN j.minutes_sur_site ELSE 0 END)
                       AS minutes_sur_site
            FROM (
                SELECT employee_id,
                       CAST(punch_time AS date) AS jour,
                       COUNT(*) AS pointages,
                       DATEDIFF(minute, MIN(punch_time), MAX(punch_time)) AS minutes_sur_site
                FROM dbo.att_punches WITH (NOLOCK)
                GROUP BY employee_id, CAST(punch_time AS date)
            ) AS j
            LEFT JOIN dbo.hr_employee AS e WITH (NOLOCK) ON e.id = j.employee_id
            LEFT JOIN dbo.hr_department AS d WITH (NOLOCK) ON d.id = e.department_id
            GROUP BY {_libelle("d.dept_name")}, j.jour
        """,
        groupe="service",
        cles=("service", "jour"),
        sommes=("personnes", "pointages", "personnes_entree_sortie", "minutes_sur_site"),
        sensibles=("minutes_sur_site",),
    ),
    # Candidatures reçues par mois et par poste (aucune donnée de candidat)
    Agregat(
        nom="candidatures_mois",
        base="RH",
        requete=f"""
            SELECT {_libelle("REPLACE(INTITULE_POSTE, '_', ' ')")} AS poste,
                   CONVERT(char(7), DATE_RECEPTION, 23) AS mois,
                   COUNT(*) AS personnes
            FROM dbo.CANDIDATURES WITH (NOLOCK)
            GROUP BY {_libelle("REPLACE(INTITULE_POSTE, '_', ' ')")},
                     CONVERT(char(7), DATE_RECEPTION, 23)
        """,
        groupe="poste",
        cles=("poste", "mois"),
        sommes=("personnes",),
    ),
)


def masquer(lignes: list[dict], agregat: Agregat, seuil: int = SEUIL_PERSONNES) -> list[dict]:
    """Fusionne les groupes de moins de ``seuil`` personnes, sans perdre les totaux.

    Une ligne sous le seuil voit sa colonne ``groupe`` remplacée par
    GROUPE_MASQUE ; les lignes de même clé sont additionnées. Si le groupe
    fusionné reste sous le seuil, ses mesures sensibles sont vidées.
    """
    fusion: dict[tuple, dict] = {}
    for ligne in lignes:
        ligne = dict(ligne)
        if (ligne["personnes"] or 0) < seuil:
            ligne[agregat.groupe] = GROUPE_MASQUE
        cle = tuple(ligne[c] for c in agregat.cles)
        if cle not in fusion:
            fusion[cle] = ligne
        else:
            cumul = fusion[cle]
            for mesure in agregat.sommes:
                cumul[mesure] = (cumul[mesure] or 0) + (ligne[mesure] or 0)
    resultat = list(fusion.values())
    for ligne in resultat:
        if ligne[agregat.groupe] == GROUPE_MASQUE and (ligne["personnes"] or 0) < seuil:
            for mesure in agregat.sensibles:
                ligne[mesure] = None
    return resultat


def _lire(curseur, requete: str) -> list[dict]:
    curseur.execute(requete)
    colonnes = [c[0] for c in curseur.description]
    return [
        {c: (int(v) if isinstance(v, Decimal) else v) for c, v in zip(colonnes, ligne, strict=True)}
        for ligne in curseur.fetchall()
    ]


def totaux_source(curseur, agregat: Agregat) -> dict[str, int]:
    """Totaux des mesures additives, calculés sur la source (pour le rapprochement)."""
    colonnes = ", ".join(f"SUM(CAST({m} AS bigint)) AS {m}" for m in agregat.sommes)
    curseur.execute(f"SELECT COUNT(*), {colonnes} FROM ({agregat.requete}) AS t")
    ligne = curseur.fetchone()
    return {m: int(v or 0) for m, v in zip(agregat.sommes, ligne[1:], strict=True)}


def main(arguments: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--simulation", action="store_true", help="contrôles seulement")
    options = parseur.parse_args(arguments)

    from ingestion.config import parametres, sources
    from ingestion.sqlserver import connecter
    from ingestion.x3 import exiger_lecture_seule

    params, source = parametres(), sources()["usine"]
    if not source.configuree:
        raise SystemExit("source « usine » non configurée dans .env")

    lots: dict[str, list[dict]] = {}
    totaux: dict[str, dict[str, int]] = {}
    charge_le = datetime.now(UTC)
    for base in sorted({a.base for a in AGREGATS}):
        with connecter(source, params, database=base) as connexion:
            exiger_lecture_seule(source, connexion, ("dbo",))
            curseur = connexion.cursor()
            for agregat in (a for a in AGREGATS if a.base == base):
                print(
                    f"usine.{base} → {SCHEMA_RAW}.{agregat.nom} : agrégé par "
                    f"{', '.join(agregat.cles)}, groupes de moins de {SEUIL_PERSONNES} fusionnés"
                )
                if options.simulation:
                    continue
                lignes = masquer(_lire(curseur, agregat.requete), agregat)
                for ligne in lignes:
                    ligne["_source"] = f"usine.{base} (agrégat)"
                    ligne["_charge_le"] = charge_le
                lots[agregat.nom] = lignes
                totaux[agregat.nom] = totaux_source(curseur, agregat)
    if options.simulation:
        print("\nSimulation : rien n'a été lu ni écrit.")
        return 0

    import dlt

    from ingestion.config import EntrepotChargeur

    pipeline = dlt.pipeline(
        pipeline_name="usine_rh",
        destination=dlt.destinations.postgres(credentials=EntrepotChargeur().identifiants_dlt()),
        dataset_name=SCHEMA_RAW,
    )
    ressources = [
        dlt.resource(lignes, name=nom, write_disposition="replace", primary_key=list(a.cles))
        for nom, lignes in lots.items()
        for a in AGREGATS
        if a.nom == nom
    ]
    print(f"\n{pipeline.run(ressources)}")
    return 0 if rapprocher(totaux) else 1


def rapprocher(totaux: dict[str, dict[str, int]]) -> bool:
    """Les totaux de l'entrepôt (après fusion des petits groupes) égalent ceux de la source."""
    import psycopg2

    from ingestion.config import EntrepotChargeur

    entrepot = EntrepotChargeur()
    connexion = psycopg2.connect(
        host=entrepot.host,
        port=entrepot.port,
        dbname=entrepot.database,
        user=entrepot.user,
        password=entrepot.password.get_secret_value(),
    )
    connexion.set_session(readonly=True)
    conforme = True
    print("\nRapprochement source / entrepôt (totaux)")
    with connexion, connexion.cursor() as curseur:
        for agregat in AGREGATS:
            colonnes = ", ".join(f"coalesce(sum({m}), 0)" for m in agregat.sommes)
            curseur.execute(f"SELECT {colonnes} FROM {SCHEMA_RAW}.{agregat.nom}")  # noqa: S608
            dw = dict(zip(agregat.sommes, (int(v) for v in curseur.fetchone()), strict=True))
            src = totaux[agregat.nom]
            # Les mesures sensibles vidées dans un petit groupe fusionné ne sont pas comparées
            ecarts = {
                m: (src[m], dw[m])
                for m in agregat.sommes
                if m not in agregat.sensibles and src[m] != dw[m]
            }
            etat = "OK" if not ecarts else f"ÉCART {ecarts}"
            conforme &= not ecarts
            print(f"  {agregat.nom:<24} {src}   {etat}")
    connexion.close()
    return conforme


if __name__ == "__main__":
    sys.exit(main())
