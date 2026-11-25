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
    from ingestion.x3_ventes import TABLES

    return rapprocher_tables(TABLES)


def rapprocher_tables(tables) -> bool:
    """Rapproche des tables copiées dans raw_x3 avec Sage X3. Vrai si tout est conforme."""
    from ingestion.x3 import SCHEMA_RAW

    source, contexte_x3, connexion_dw = _connexions()
    resultats = []
    try:
        with contexte_x3 as connexion_x3, connexion_dw.cursor() as curseur_dw:
            curseur_x3 = connexion_x3.cursor()
            for table in tables:
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


# ─── Créances et dettes ouvertes : Sage X3 / marts.fct_echeances ─────
#
# Même règle des deux côtés (docs/indicateurs/finance_creances.md) :
#   reste à payer = (montant - payé) × signe, échéances ouvertes (≥ 0,01 MAD)

REQUETE_RESTES_X3 = """
SELECT CASE BPRTYP_0 WHEN 1 THEN 'client' WHEN 2 THEN 'fournisseur' END AS type_tiers,
       COUNT(*) AS echeances,
       SUM((CAST(AMTLOC_0 AS DECIMAL(28, 4)) - CAST(PAYLOC_0 AS DECIMAL(28, 4))) * SNS_0) AS reste
FROM {dossier}.GACCDUDATE
WHERE ABS(AMTLOC_0 - PAYLOC_0) >= 0.01
  AND LTRIM(RTRIM(NUM_0)) <> ''
  AND BPRTYP_0 IN (1, 2)
GROUP BY BPRTYP_0
"""

REQUETE_RESTES_ENTREPOT = """
SELECT type_tiers, count(*), sum(reste_a_payer)
FROM marts.fct_echeances
WHERE est_ouverte
GROUP BY type_tiers
"""


def rapprocher_creances() -> bool:
    """Restes à payer ouverts, clients et fournisseurs : Sage X3 contre l'entrepôt."""
    source, contexte_x3, connexion_dw = _connexions()
    try:
        with contexte_x3 as connexion_x3, connexion_dw.cursor() as curseur_dw:
            curseur_x3 = connexion_x3.cursor()
            curseur_x3.execute(REQUETE_RESTES_X3.format(dossier=_id(source.dossier)))
            x3 = {t: Mesure(int(n), Decimal(m)) for t, n, m in curseur_x3.fetchall()}
            curseur_dw.execute(REQUETE_RESTES_ENTREPOT)
            dw = {t: Mesure(int(n), Decimal(m)) for t, n, m in curseur_dw.fetchall()}
    finally:
        connexion_dw.close()

    resultats = [
        Resultat(
            table=t,
            source=x3.get(t, Mesure(0, Decimal(0))),
            entrepot=dw.get(t, Mesure(0, Decimal(0))),
        )
        for t in ("client", "fournisseur")
    ]
    print("\nÉchéances ouvertes : nombre et reste à payer (MAD)")
    afficher(resultats)
    return all(r.conforme for r in resultats)


# ─── Résultat par exercice : BALANCE de Sage X3 / marts.fct_ecritures ─
#
# BALANCE est tenue par Sage X3 lui-même (cumuls débit et crédit par
# compte et par période, colonnes DEBLED_0 … DEBLED_27). L'entrepôt part
# des LIGNES d'écritures. Deux chemins indépendants vers le même chiffre :
#   résultat = - (débits - crédits) des comptes des classes 6 et 7
# La BALANCE contient les écritures de clôture : un exercice clôturé y vaut 0.
# Le rapprochement compare donc TOUTES les écritures, clôture comprise ; le
# résultat de gestion (hors clôture) est affiché à côté, pour information.

PERIODES_BALANCE = range(28)  # DEBLED_0 … DEBLED_27 : à-nouveaux + périodes

REQUETE_RESULTAT_X3 = """
SELECT FIY_0 AS exercice,
       -SUM(({debits}) - ({credits})) AS resultat
FROM {dossier}.BALANCE
WHERE LEDTYP_0 = 1
  AND (ACC_0 LIKE '6%' OR ACC_0 LIKE '7%')
  -- BALANCE a une ligne par site et par tiers ET une ligne de total (site et
  -- tiers vides) : on ne lit que les totaux, sinon tout est compté deux fois
  AND LTRIM(RTRIM(FCY_0)) = ''
  AND LTRIM(RTRIM(BPR_0)) = ''
GROUP BY FIY_0
"""

REQUETE_RESULTAT_ENTREPOT = """
SELECT numero_exercice, -sum(solde)
FROM marts.fct_ecritures
WHERE classe IN ('6', '7')
GROUP BY numero_exercice
"""

REQUETE_RESULTAT_GESTION = """
SELECT numero_exercice, sum(montant_resultat)
FROM marts.agg_compte_de_resultat_mois
GROUP BY numero_exercice
"""


def requete_resultat_x3(dossier: str) -> str:
    def colonnes(prefixe: str) -> str:
        return " + ".join(f"CAST({prefixe}_{i} AS DECIMAL(28, 4))" for i in PERIODES_BALANCE)

    return REQUETE_RESULTAT_X3.format(
        dossier=_id(dossier), debits=colonnes("DEBLED"), credits=colonnes("CDTLED")
    )


def rapprocher_resultat() -> bool:
    """Résultat par exercice : BALANCE de Sage X3 contre l'entrepôt."""
    source, contexte_x3, connexion_dw = _connexions()
    try:
        with contexte_x3 as connexion_x3, connexion_dw.cursor() as curseur_dw:
            curseur_x3 = connexion_x3.cursor()
            curseur_x3.execute(requete_resultat_x3(source.dossier))
            x3 = {int(a): Decimal(m) for a, m in curseur_x3.fetchall()}
            curseur_dw.execute(REQUETE_RESULTAT_ENTREPOT)
            dw = {int(a): Decimal(m) for a, m in curseur_dw.fetchall()}
            curseur_dw.execute(REQUETE_RESULTAT_GESTION)
            gestion = {int(a): Decimal(m) for a, m in curseur_dw.fetchall()}
    finally:
        connexion_dw.close()

    lignes = comparer_ca(x3, dw)
    print("\nClasses 6 et 7, clôture comprise : BALANCE X3 / entrepôt")
    print(
        f"  {'exerc.':6s} {'Sage X3':>18s} {'entrepôt':>18s}   {'écart':8s}"
        f" {'résultat hors clôture':>22s}"
    )
    for exercice, cote_x3, cote_dw, ok in lignes:
        etat = "OK" if ok else f"ÉCART {cote_dw - cote_x3:+,.2f}"
        hors_cloture = gestion.get(exercice, Decimal(0))
        print(
            f"  {exercice:<6d} {cote_x3:>18,.2f} {cote_dw:>18,.2f}   {etat:8s}"
            f" {hors_cloture:>22,.2f}"
        )
    return all(ok for *_, ok in lignes)


# ─── Trésorerie : soldes de fin d'exercice, compte par compte ─────────

REQUETE_TRESORERIE_X3 = """
SELECT FIY_0, LTRIM(RTRIM(ACC_0)), SUM(({debits}) - ({credits}))
FROM {dossier}.BALANCE
WHERE LEDTYP_0 = 1
  AND (ACC_0 LIKE '51%' OR ACC_0 LIKE '55%')
  AND LTRIM(RTRIM(FCY_0)) = ''   -- lignes de total : site vide…
  AND LTRIM(RTRIM(BPR_0)) = ''   -- … et tiers vide (sinon chèques et effets comptent double)
  -- Exercices déjà commencés : X3 reporte d'avance les soldes dans l'exercice suivant
  AND FIY_0 IN (SELECT FIYNUM_0 FROM {dossier}.FISCALYEAR
                WHERE LEDTYP_0 = 1 AND FIYSTR_0 <= GETDATE())
GROUP BY FIY_0, LTRIM(RTRIM(ACC_0))
"""

# Le dernier solde_fin_jour d'un exercice = somme de ses mouvements.
# Soldes à ce jour : les écritures datées dans le futur (erreurs de saisie,
# signalées par un test dbt) sont ignorées, comme dans la BALANCE.
REQUETE_TRESORERIE_ENTREPOT = """
SELECT numero_exercice, compte, sum(mouvement)
FROM marts.agg_tresorerie_jour
WHERE date_jour <= current_date
GROUP BY numero_exercice, compte
"""


def comparer_soldes(
    source: dict[tuple[int, str], Decimal], entrepot: dict[tuple[int, str], Decimal]
) -> dict[int, tuple[Decimal, Decimal, list[str]]]:
    """Par exercice : total source, total entrepôt, comptes en écart (≥ 0,01)."""
    resultat: dict[int, tuple[Decimal, Decimal, list[str]]] = {}
    for exercice, compte in sorted(set(source) | set(entrepot)):
        cote_source = source.get((exercice, compte), Decimal(0))
        cote_entrepot = entrepot.get((exercice, compte), Decimal(0))
        total_source, total_entrepot, ecarts = resultat.get(exercice, (Decimal(0), Decimal(0), []))
        if abs(cote_entrepot - cote_source) >= TOLERANCE_MONTANT:
            ecarts = [*ecarts, compte]
        resultat[exercice] = (total_source + cote_source, total_entrepot + cote_entrepot, ecarts)
    return resultat


def rapprocher_tresorerie() -> bool:
    """Soldes de fin d'exercice des comptes 51 et 55 : BALANCE X3 contre l'entrepôt."""
    source, contexte_x3, connexion_dw = _connexions()
    debits = " + ".join(f"CAST(DEBLED_{i} AS DECIMAL(28, 4))" for i in PERIODES_BALANCE)
    credits = " + ".join(f"CAST(CDTLED_{i} AS DECIMAL(28, 4))" for i in PERIODES_BALANCE)
    try:
        with contexte_x3 as connexion_x3, connexion_dw.cursor() as curseur_dw:
            curseur_x3 = connexion_x3.cursor()
            curseur_x3.execute(
                REQUETE_TRESORERIE_X3.format(
                    dossier=_id(source.dossier), debits=debits, credits=credits
                )
            )
            x3 = {(int(e), c): Decimal(m) for e, c, m in curseur_x3.fetchall()}
            curseur_dw.execute(REQUETE_TRESORERIE_ENTREPOT)
            dw = {(int(e), c): Decimal(m) for e, c, m in curseur_dw.fetchall()}
    finally:
        connexion_dw.close()

    resultat = comparer_soldes(x3, dw)
    print("\nTrésorerie (comptes 51 et 55), solde de fin d'exercice : BALANCE X3 / entrepôt")
    for exercice, (total_x3, total_dw, ecarts) in resultat.items():
        etat = "OK" if not ecarts else f"ÉCART sur {len(ecarts)} compte(s) : {ecarts[:5]}"
        print(f"  {exercice:<4d} {total_x3:>18,.2f} {total_dw:>18,.2f}   {etat}")
    return all(not ecarts for *_, ecarts in resultat.values())


# ─── Stock valorisé par site : Sage X3 / marts.fct_stock_article ──────

REQUETE_STOCK_X3 = """
SELECT LTRIM(RTRIM(STOFCY_0)), COUNT(*),
       SUM(CAST(PHYSTO_0 AS DECIMAL(28, 6)) * CAST(AVC_0 AS DECIMAL(28, 6)))
FROM {dossier}.ITMMVT
GROUP BY LTRIM(RTRIM(STOFCY_0))
"""

REQUETE_STOCK_ENTREPOT = """
SELECT site, count(*), sum(valeur_stock)
FROM marts.fct_stock_article
GROUP BY site
"""


def rapprocher_stock() -> bool:
    """Stock valorisé (stock physique × CMUP) par site : Sage X3 contre l'entrepôt."""
    source, contexte_x3, connexion_dw = _connexions()
    try:
        with contexte_x3 as connexion_x3, connexion_dw.cursor() as curseur_dw:
            curseur_x3 = connexion_x3.cursor()
            curseur_x3.execute(REQUETE_STOCK_X3.format(dossier=_id(source.dossier)))
            x3 = {s: Mesure(int(n), Decimal(v)) for s, n, v in curseur_x3.fetchall()}
            curseur_dw.execute(REQUETE_STOCK_ENTREPOT)
            dw = {s: Mesure(int(n), Decimal(v)) for s, n, v in curseur_dw.fetchall()}
    finally:
        connexion_dw.close()

    vide = Mesure(0, Decimal(0))
    resultats = [
        Resultat(table=f"site {s}", source=x3.get(s, vide), entrepot=dw.get(s, vide))
        for s in sorted(set(x3) | set(dw))
    ]
    print("\nStock valorisé par site (articles, MAD)")
    afficher(resultats)
    return all(r.conforme for r in resultats)


# ─── Dépense d'achat par année : Sage X3 / marts.fct_achats_factures ──
#
# On compare les LIGNES de factures des deux côtés, avec la même
# conversion en MAD (taux de l'entête). L'écart entre les entêtes et les
# lignes de Sage X3 lui-même (factures dont l'entête ne correspond pas à
# ses lignes) est affiché à part : c'est une anomalie de la source, listée
# par le test dbt assert_x3_facture_fournisseur_entete_egal_lignes.

REQUETE_ACHATS_X3 = """
-- Lignes additionnées par facture, puis converties en MAD en multipliant
-- AVANT de diviser : SQL Server tronque sinon les décimales du taux.
SELECT YEAR(l.ACCDAT_0),
       SUM(l.lignes * h.SNS_0 * CASE WHEN h.AMTNOT_0 <> 0
                                     THEN CAST(h.AMTNOTL_0 AS DECIMAL(28, 6)) END
           / CASE WHEN h.AMTNOT_0 <> 0 THEN CAST(h.AMTNOT_0 AS DECIMAL(28, 6)) END)
       + SUM(CASE WHEN h.AMTNOT_0 = 0 THEN l.lignes * h.SNS_0 ELSE 0 END)
FROM (SELECT NUM_0, ACCDAT_0, SUM(CAST(AMTNOTLIN_0 AS DECIMAL(28, 6))) AS lignes
      FROM {dossier}.PINVOICED
      WHERE LTRIM(RTRIM(NUM_0)) <> ''
      GROUP BY NUM_0, ACCDAT_0) AS l
JOIN {dossier}.PINVOICE h ON h.NUM_0 = l.NUM_0
GROUP BY YEAR(l.ACCDAT_0)
"""

REQUETE_ACHATS_ENTETES_X3 = """
SELECT YEAR(ACCDAT_0), SUM(CAST(AMTNOTL_0 AS DECIMAL(28, 4)) * SNS_0)
FROM {dossier}.PINVOICE
WHERE LTRIM(RTRIM(NUM_0)) <> ''
GROUP BY YEAR(ACCDAT_0)
"""

REQUETE_ACHATS_ENTREPOT = """
SELECT extract(year FROM date_comptable)::int, sum(montant_ht_mad_signe)
FROM marts.fct_achats_factures
GROUP BY 1
"""


def rapprocher_achats() -> bool:
    """Dépense d'achat HT par année (lignes) : Sage X3 contre l'entrepôt."""
    source, contexte_x3, connexion_dw = _connexions()
    dossier = _id(source.dossier)
    try:
        with contexte_x3 as connexion_x3, connexion_dw.cursor() as curseur_dw:
            curseur_x3 = connexion_x3.cursor()
            curseur_x3.execute(REQUETE_ACHATS_X3.format(dossier=dossier))
            x3 = {int(a): Decimal(m) for a, m in curseur_x3.fetchall()}
            curseur_x3.execute(REQUETE_ACHATS_ENTETES_X3.format(dossier=dossier))
            entetes = {int(a): Decimal(m) for a, m in curseur_x3.fetchall()}
            curseur_dw.execute(REQUETE_ACHATS_ENTREPOT)
            dw = {int(a): Decimal(m) for a, m in curseur_dw.fetchall()}
    finally:
        connexion_dw.close()

    lignes = comparer_ca(x3, dw)
    print("\nDépense d'achat HT par année (MAD, avoirs déduits), lignes de factures")
    print(
        f"  {'année':6s} {'Sage X3':>18s} {'entrepôt':>18s}   {'écart':8s}"
        f" {'entêtes X3 - lignes X3':>24s}"
    )
    for annee, cote_x3, cote_dw, ok in lignes:
        etat = "OK" if ok else f"ÉCART {cote_dw - cote_x3:+,.2f}"
        interne = entetes.get(annee, Decimal(0)) - cote_x3
        print(f"  {annee:<6d} {cote_x3:>18,.2f} {cote_dw:>18,.2f}   {etat:8s} {interne:>24,.2f}")
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
    parseur.add_argument("--creances", action="store_true", help="restes à payer ouverts contre X3")
    parseur.add_argument(
        "--resultat", action="store_true", help="résultat par exercice contre la BALANCE X3"
    )
    parseur.add_argument(
        "--tresorerie", action="store_true", help="soldes de trésorerie contre la BALANCE X3"
    )
    parseur.add_argument("--stock", action="store_true", help="stock valorisé par site contre X3")
    parseur.add_argument(
        "--achats", action="store_true", help="dépense d'achat par année contre X3"
    )
    options = parseur.parse_args(arguments)
    tout = not (
        options.raw
        or options.ca
        or options.creances
        or options.resultat
        or options.tresorerie
        or options.stock
        or options.achats
    )
    conforme = True
    if options.raw or tout:
        conforme &= rapprocher_x3_ventes()
    if options.ca or tout:
        conforme &= rapprocher_ca_annuel()
    if options.creances or tout:
        conforme &= rapprocher_creances()
    if options.resultat or tout:
        conforme &= rapprocher_resultat()
    if options.tresorerie or tout:
        conforme &= rapprocher_tresorerie()
    if options.stock or tout:
        conforme &= rapprocher_stock()
    if options.achats or tout:
        conforme &= rapprocher_achats()
    return 0 if conforme else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
