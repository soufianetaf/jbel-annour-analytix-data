"""Rôles de la plateforme et domaines que chacun peut lire (cahier des charges, rôles).

C'est la SEULE table des droits : chaque route déclare son domaine, et
l'accès est refusé (403) à tout rôle qui n'est pas listé ici. Un domaine
oublié ici n'est ouvert à personne.

Le représentant ne voit que ses propres ventes : ce filtre-là est appliqué
dans la requête SQL (api/routes/ventes.py), avec son code Sage X3.
"""

from __future__ import annotations

ROLES = (
    "direction",
    "commercial",
    "representant",
    "production",
    "maintenance",
    "achats",
    "finance",
    "rh",
    "administrateur",
)

DOMAINES: dict[str, frozenset[str]] = {
    # Ventes : la direction, le commercial, la finance ; le représentant, filtré
    "ventes": frozenset({"direction", "commercial", "representant", "finance"}),
    # Tableau de bord de la direction (coût, marge, trésorerie)
    "direction": frozenset({"direction", "finance"}),
    # RH agrégée : seul le rôle RH, et la direction pour les agrégats
    "rh": frozenset({"direction", "rh"}),
    # Qualité des données : nombre de lignes à corriger par service, sans
    # donnée métier ; ouvert à tous, administrateur compris
    "qualite_donnees": frozenset(ROLES),
}


def peut_lire(role: str, domaine: str) -> bool:
    return role in DOMAINES.get(domaine, frozenset())
