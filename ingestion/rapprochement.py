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


def mesurer_source(curseur, dossier: str, table: str, montant: str) -> Mesure:
    """Compte et somme dans Sage X3 (session sans verrou, voir sqlserver.connecter)."""
    curseur.execute(
        f"SELECT COUNT(*), COALESCE(SUM(CAST({_id(montant)} AS DECIMAL(28, 4))), 0) "
        f"FROM {_id(dossier)}.{_id(table)}"
    )
    lignes, somme = curseur.fetchone()
    return Mesure(lignes=int(lignes), montant=Decimal(somme))


def mesurer_entrepot(
    curseur, schema: str, table: str, montant: str, cle: tuple[str, ...]
) -> Mesure:
    """Compte, somme et doublons de clé dans la couche raw (noms en minuscules)."""
    colonnes_cle = ", ".join(_id(c.lower()) for c in cle)
    curseur.execute(
        f"SELECT COUNT(*), COALESCE(SUM({_id(montant.lower())}), 0), "
        f"COUNT(*) - COUNT(DISTINCT ({colonnes_cle})) "
        f"FROM {_id(schema)}.{_id(table.lower())}"
    )
    lignes, somme, doublons = curseur.fetchone()
    return Mesure(lignes=int(lignes), montant=Decimal(somme), doublons=int(doublons))


def afficher(resultats: list[Resultat]) -> None:
    print("\nRapprochement source / entrepôt")
    for r in resultats:
        etat = "OK" if r.conforme else "ÉCART : " + ", ".join(r.problemes)
        print(
            f"  {r.table:10s} lignes {r.source.lignes:>8,d} / {r.entrepot.lignes:>8,d}   "
            f"montant {r.source.montant:>20,.2f} / {r.entrepot.montant:>20,.2f}   {etat}"
        )


def rapprocher_x3_ventes() -> bool:
    """Rapproche les tables de ingestion.x3_ventes. Vrai si tout est conforme."""
    import psycopg2

    from ingestion.config import EntrepotChargeur, parametres, sources
    from ingestion.sqlserver import connecter
    from ingestion.x3_ventes import SCHEMA_RAW, TABLES

    source = sources()["x3"]
    entrepot = EntrepotChargeur()
    resultats = []

    with connecter(source, parametres()) as connexion_x3:
        curseur_x3 = connexion_x3.cursor()
        connexion_dw = psycopg2.connect(**_identifiants_psycopg(entrepot))
        connexion_dw.set_session(readonly=True)
        try:
            with connexion_dw.cursor() as curseur_dw:
                for table in TABLES:
                    resultats.append(
                        Resultat(
                            table=table.nom,
                            source=mesurer_source(
                                curseur_x3, source.dossier, table.nom, table.montant
                            ),
                            entrepot=mesurer_entrepot(
                                curseur_dw, SCHEMA_RAW, table.nom, table.montant, table.cle
                            ),
                        )
                    )
        finally:
            connexion_dw.close()

    afficher(resultats)
    return all(r.conforme for r in resultats)


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
