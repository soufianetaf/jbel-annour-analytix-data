"""Alertes de la direction : seuils, tri, liste vide quand rien ne va mal."""

from __future__ import annotations

# ─── Alertes de la direction ─────────────────────────────────────────


class EntrepotAlertes:
    """Répond aux requêtes des alertes par des valeurs choisies."""

    def __init__(self, reponses: dict[str, list[dict]]) -> None:
        self.reponses = reponses

    def lire(self, sql: str, parametres=None, perimetre: str = "") -> list[dict]:
        for table, lignes in self.reponses.items():
            if f"marts.{table}" in sql:
                return lignes
        return []


def test_alertes_triees_du_plus_grave_au_moins_grave():
    from api.routes.direction import calculer_alertes

    entrepot = EntrepotAlertes(
        {
            "fct_livraisons": [{"livraisons": 681, "montant": 11_908_090, "plus_ancienne": 25}],
            "fct_commandes": [{"commandes": 174, "montant": 6_414_007}],
            "fct_machines_jour": [{"machine": "depileuse"}],
            "fct_electricite_jour": [],
            "agg_qualite_donnees": [{"lignes": 503, "services": 10}],
        }
    )
    alertes = calculer_alertes(entrepot)
    assert [a.niveau for a in alertes] == ["critique", "attention", "information", "information"]
    assert alertes[0].code == "automate_sans_heures_depileuse"
    assert alertes[0].titre == "L'automate de la dépileuse ne compte plus ses heures"
    assert alertes[1].titre == "174 commandes soldées sans livraison"
    livre = next(a for a in alertes if a.code == "livre_non_facture")
    assert livre.titre == "11,91 M MAD livrés, pas encore facturés"
    assert livre.niveau == "information"  # 25 jours : dans la facturation mensuelle


def test_rien_a_signaler_donne_une_liste_vide():
    from api.routes.direction import calculer_alertes

    entrepot = EntrepotAlertes(
        {
            "fct_livraisons": [{"livraisons": 0, "montant": 0, "plus_ancienne": None}],
            "fct_commandes": [{"commandes": 0, "montant": 0}],
            "agg_qualite_donnees": [{"lignes": 0, "services": 0}],
        }
    )
    assert calculer_alertes(entrepot) == []


def test_livraison_non_facturee_depuis_plus_de_45_jours_est_critique():
    from api.routes.direction import calculer_alertes

    entrepot = EntrepotAlertes(
        {
            "fct_livraisons": [{"livraisons": 3, "montant": 50_000, "plus_ancienne": 60}],
            "fct_commandes": [{"commandes": 0, "montant": 0}],
            "agg_qualite_donnees": [{"lignes": 0, "services": 0}],
        }
    )
    assert calculer_alertes(entrepot)[0].niveau == "critique"
