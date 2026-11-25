"""Rapprochement chiffré : la copie dans l'entrepôt retrouve-t-elle la source ?

Pour chaque table copiée, on compare la source et la couche raw :

- le **nombre de lignes** : doit être identique ;
- la **somme d'un montant** : écart inférieur à 0,01 MAD (critère
  d'acceptation n° 1 du cahier des charges) ;
- l'**unicité de la clé** dans l'entrepôt : aucun doublon.

Sage X3 tourne en continu : une facture saisie entre la copie et le
rapprochement crée un écart. Relancer la copie le fait disparaître ; un
écart qui persiste signale un vrai problème.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

TOLERANCE_MONTANT = Decimal("0.01")
_IDENTIFIANT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Mesure:
    lignes: int
    montant: Decimal
    doublons: int = 0


@dataclass(frozen=True)
class Resultat:
    table: str
    source: Mesure
    entrepot: Mesure

    @property
    def ecart_lignes(self) -> int:
        return self.entrepot.lignes - self.source.lignes

    @property
    def ecart_montant(self) -> Decimal:
        return self.entrepot.montant - self.source.montant

    @property
    def problemes(self) -> list[str]:
        problemes = []
        if self.ecart_lignes:
            problemes.append(f"{self.ecart_lignes:+d} ligne(s)")
        if abs(self.ecart_montant) >= TOLERANCE_MONTANT:
            problemes.append(f"écart de montant {self.ecart_montant:+,.2f}")
        if self.entrepot.doublons:
            problemes.append(f"{self.entrepot.doublons} doublon(s) sur la clé")
        return problemes

    @property
    def conforme(self) -> bool:
        return not self.problemes


def _id(nom: str) -> str:
    if not _IDENTIFIANT.match(nom):
        raise ValueError(f"identifiant invalide : {nom}")
    return nom


def mesurer_source(curseur, dossier: str, table: str, montant: str | None) -> Mesure:
    """Compte et somme dans Sage X3 (session sans verrou, voir sqlserver.connecter)."""
    somme = f"CAST({_id(montant)} AS DECIMAL(28, 4))" if montant else "0"
    curseur.execute(f"SELECT COUNT(*), COALESCE(SUM({somme}), 0) FROM {_id(dossier)}.{_id(table)}")
    lignes, total = curseur.fetchone()
    return Mesure(lignes=int(lignes), montant=Decimal(total))


def mesurer_entrepot(
    curseur, schema: str, table: str, montant: str | None, cle: tuple[str, ...]
) -> Mesure:
    """Compte, somme et doublons de clé dans la couche raw (noms en minuscules)."""
    colonnes_cle = ", ".join(_id(c.lower()) for c in cle)
    somme = _id(montant.lower()) if montant else "0"
    curseur.execute(
        f"SELECT COUNT(*), COALESCE(SUM({somme}), 0), "
        f"COUNT(*) - COUNT(DISTINCT ({colonnes_cle})) "
        f"FROM {_id(schema)}.{_id(table.lower())}"
    )
    lignes, total, doublons = curseur.fetchone()
    return Mesure(lignes=int(lignes), montant=Decimal(total), doublons=int(doublons))


def afficher(resultats: list[Resultat]) -> None:
    print("\nRapprochement source / entrepôt")
    for r in resultats:
        etat = "OK" if r.conforme else "ÉCART : " + ", ".join(r.problemes)
        print(
            f"  {r.table:10s} lignes {r.source.lignes:>8,d} / {r.entrepot.lignes:>8,d}   "
            f"montant {r.source.montant:>20,.2f} / {r.entrepot.montant:>20,.2f}   {etat}"
        )


def _connexions():
    """Connexion à Sage X3 (lecture seule, sans verrou) et à l'entrepôt (lecture seule)."""
    import psycopg2

    from ingestion.config import EntrepotChargeur, parametres, sources
    from ingestion.sqlserver import connecter

    source = sources()["x3"]
    connexion_dw = psycopg2.connect(**_identifiants_psycopg(EntrepotChargeur()))
    connexion_dw.set_session(readonly=True)
    return source, connecter(source, parametres()), connexion_dw


def rapprocher_x3_ventes() -> bool:
    """Rapproche les tables copiées par ingestion.x3_ventes. Vrai si tout est conforme."""
    from ingestion.x3_ventes import SCHEMA_RAW, TABLES

    source, contexte_x3, connexion_dw = _connexions()
    resultats = []
    try:
        with contexte_x3 as connexion_x3, connexion_dw.cursor() as curseur_dw:
            curseur_x3 = connexion_x3.cursor()
            for table in TABLES:
                resultats.append(
                    Resultat(
                        table=table.nom,
                        source=mesurer_source(curseur_x3, source.dossier, table.nom, table.montant),
                        entrepot=mesurer_entrepot(
                            curseur_dw, SCHEMA_RAW, table.nom, table.montant, table.cle
                        ),
                    )
                )
    finally:
        connexion_dw.close()

    afficher(resultats)
    return all(r.conforme for r in resultats)


# ─── CA net par année : Sage X3 / marts.fct_ventes ───────────────────
#
# Même définition des deux côtés (docs/indicateurs/ventes_ca_net.md),
# mais par deux chemins indépendants : les ENTÊTES dans Sage X3, les
# LIGNES dans l'entrepôt. Si l'un des deux calculs se trompe, ils divergent.

REQUETE_CA_X3 = """
SELECT YEAR(ACCDAT_0) AS annee,
       SUM(CAST(AMTNOT_0 AS DECIMAL(28, 4)) * SNS_0) AS ca_net
FROM {dossier}.SINVOICE
WHERE SIVTYP_0 <> 'PRF'          -- pro forma exclues
  AND LTRIM(RTRIM(NUM_0)) <> ''  -- entête technique vide exclu
GROUP BY YEAR(ACCDAT_0)
"""

REQUETE_CA_ENTREPOT = """
SELECT extract(year FROM date_comptable)::int AS annee, sum(montant_ht_signe) AS ca_net
FROM marts.fct_ventes
GROUP BY 1
"""


def comparer_ca(
    source: dict[int, Decimal], entrepot: dict[int, Decimal]
) -> list[tuple[int, Decimal, Decimal, bool]]:
    """Compare le CA par année. Une année absente d'un côté vaut 0 (donc un écart)."""
    annees = sorted(set(source) | set(entrepot))
    lignes = []
    for annee in annees:
        cote_source = source.get(annee, Decimal(0))
        cote_entrepot = entrepot.get(annee, Decimal(0))
        conforme = abs(cote_entrepot - cote_source) < TOLERANCE_MONTANT
        lignes.append((annee, cote_source, cote_entrepot, conforme))
    return lignes


def rapprocher_ca_annuel() -> bool:
    """CA net par année : Sage X3 contre marts.fct_ventes. Vrai si tout est conforme."""
    source, contexte_x3, connexion_dw = _connexions()
    try:
        with contexte_x3 as connexion_x3, connexion_dw.cursor() as curseur_dw:
            curseur_x3 = connexion_x3.cursor()
            curseur_x3.execute(REQUETE_CA_X3.format(dossier=_id(source.dossier)))
            ca_x3 = {int(a): Decimal(m) for a, m in curseur_x3.fetchall()}
            curseur_dw.execute(REQUETE_CA_ENTREPOT)
            ca_dw = {int(a): Decimal(m) for a, m in curseur_dw.fetchall()}
    finally:
        connexion_dw.close()

    lignes = comparer_ca(ca_x3, ca_dw)
    print("\nCA net par année (HT, avoirs déduits, hors pro forma)")
    print(f"  {'année':6s} {'Sage X3':>20s} {'entrepôt':>20s}   écart")
    for annee, x3, dw, ok in lignes:
        etat = "OK" if ok else f"ÉCART {dw - x3:+,.2f}"
        print(f"  {annee:<6d} {x3:>20,.2f} {dw:>20,.2f}   {etat}")
    total_x3, total_dw = sum(ca_x3.values(), Decimal(0)), sum(ca_dw.values(), Decimal(0))
    print(f"  {'total':6s} {total_x3:>20,.2f} {total_dw:>20,.2f}")
    return all(ok for *_, ok in lignes)


def _identifiants_psycopg(entrepot) -> dict:
    ident = entrepot.identifiants_dlt()
    return {
        "host": ident["host"],
        "port": ident["port"],
        "dbname": ident["database"],
        "user": ident["username"],
        "password": ident["password"],
        "connect_timeout": 10,
    }


def main(arguments: list[str] | None = None) -> int:
    import argparse

    parseur = argparse.ArgumentParser(description="Rapprochements chiffrés avec Sage X3")
    parseur.add_argument("--raw", action="store_true", help="copies raw_x3 contre X3")
    parseur.add_argument("--ca", action="store_true", help="CA net par année contre X3")
    options = parseur.parse_args(arguments)
    tout = not (options.raw or options.ca)
    conforme = True
    if options.raw or tout:
        conforme &= rapprocher_x3_ventes()
    if options.ca or tout:
        conforme &= rapprocher_ca_annuel()
    return 0 if conforme else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
