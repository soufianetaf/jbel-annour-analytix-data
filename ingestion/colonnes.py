"""Choix des colonnes copiées : aucune donnée sensible n'entre dans l'entrepôt.

Règle d'or n° 2 : mots de passe, jetons, CIN, RIB, salaires individuels ne
sont jamais copiés. Les colonnes sont filtrées **avant** la lecture : la
requête envoyée à la source ne les demande même pas.

Le contrôle repère les noms de colonnes qui ressemblent à une donnée
sensible. Chaque colonne repérée doit avoir été **décidée** explicitement
pour la table : exclue, ou autorisée après vérification. Une colonne
repérée mais non décidée arrête le chargement : on ne copie rien par
défaut quand on a un doute.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Morceaux de noms de colonnes qui signalent une donnée possiblement sensible.
# Dans Sage X3, les noms sont des abréviations : PAYBAN_0 = banque de paiement.
MOTIFS_SENSIBLES = re.compile(
    r"PASS|PWD|MDP|TOKEN|JETON|SECRET|IBAN|RIB|BAN_|CIN|CNSS|CNIE|PASSPORT|"
    r"SALAIRE|SALARY|SALBRU|SALNET|SALBAS",
    re.IGNORECASE,
)


class ColonneSensibleNonDecidee(Exception):
    """Une colonne ressemble à une donnée sensible et n'a été ni exclue ni autorisée."""


def colonnes_a_copier(
    colonnes: Iterable[str],
    exclues: Iterable[str] = (),
    autorisees: Iterable[str] = (),
    seulement: Iterable[str] | None = None,
) -> list[str]:
    """Liste des colonnes à copier, dans l'ordre de la source.

    - ``exclues``    : jamais copiées (données sensibles ou inutiles) ;
    - ``autorisees`` : repérées par le contrôle, mais vérifiées et sans risque ;
    - ``seulement``  : liste fermée. Si elle est donnée, SEULES ces colonnes
      sont copiées : une colonne ajoutée plus tard dans la source n'entre
      jamais sans décision. À utiliser pour les tables qui contiennent des
      données sensibles (ex. fiche client : CIN du gérant, banque).
    """
    exclues, autorisees = set(exclues), set(autorisees)
    colonnes = list(colonnes)

    decidees = exclues | autorisees | set(seulement or ())
    inconnues = decidees - set(colonnes)
    if inconnues:
        # Une colonne décidée qui n'existe plus : la source a changé de structure
        raise ValueError(f"colonnes décidées absentes de la source : {sorted(inconnues)}")

    if seulement is not None:
        liste = set(seulement)
        colonnes = [nom for nom in colonnes if nom in liste]

    non_decidees = [
        nom
        for nom in colonnes
        if MOTIFS_SENSIBLES.search(nom) and nom not in exclues and nom not in autorisees
    ]
    if non_decidees:
        raise ColonneSensibleNonDecidee(
            f"colonnes possiblement sensibles, à exclure ou autoriser : {non_decidees}"
        )

    return [nom for nom in colonnes if nom not in exclues]
