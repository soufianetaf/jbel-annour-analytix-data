"""Copie RH agrégée : aucun petit groupe ni donnée individuelle ne sort de la source."""

import re

from ingestion.usine_rh import AGREGATS, GROUPE_MASQUE, SEUIL_PERSONNES, Agregat, masquer

POINTAGE = Agregat(
    nom="test",
    base="pointage",
    requete="",
    groupe="service",
    cles=("service", "jour"),
    sommes=("personnes", "minutes_sur_site"),
    sensibles=("minutes_sur_site",),
)


def test_un_petit_groupe_est_fusionne_sans_perdre_les_totaux():
    lignes = [
        {"service": "PRODUCTION", "jour": "2026-10-01", "personnes": 40, "minutes_sur_site": 19200},
        {"service": "JURIDIQUE", "jour": "2026-10-01", "personnes": 1, "minutes_sur_site": 240},
        {"service": "ACHATS", "jour": "2026-10-01", "personnes": 3, "minutes_sur_site": 1500},
        {"service": "RH", "jour": "2026-10-01", "personnes": 2, "minutes_sur_site": 960},
    ]
    resultat = {ligne["service"]: ligne for ligne in masquer(lignes, POINTAGE)}
    assert set(resultat) == {"PRODUCTION", GROUPE_MASQUE}
    # 1 + 3 + 2 = 6 personnes : le groupe fusionné atteint le seuil, ses mesures restent
    assert resultat[GROUPE_MASQUE]["personnes"] == 6
    assert resultat[GROUPE_MASQUE]["minutes_sur_site"] == 2700
    assert sum(r["personnes"] for r in resultat.values()) == 46


def test_un_groupe_fusionne_encore_petit_perd_ses_mesures_sensibles():
    lignes = [
        {"service": "PRODUCTION", "jour": "2026-10-01", "personnes": 40, "minutes_sur_site": 19200},
        {"service": "JURIDIQUE", "jour": "2026-10-01", "personnes": 1, "minutes_sur_site": 240},
    ]
    resultat = {ligne["service"]: ligne for ligne in masquer(lignes, POINTAGE)}
    assert resultat[GROUPE_MASQUE]["personnes"] == 1  # le comptage reste
    assert resultat[GROUPE_MASQUE]["minutes_sur_site"] is None  # le temps d'une personne, non


def test_aucune_ligne_ecrite_sous_le_seuil_avec_son_nom():
    lignes = [
        {"service": f"S{i}", "jour": "2026-10-01", "personnes": i, "minutes_sur_site": i}
        for i in range(1, 9)
    ]
    for ligne in masquer(lignes, POINTAGE):
        assert ligne["personnes"] >= SEUIL_PERSONNES or ligne["service"] == GROUPE_MASQUE


# Colonnes de personnes dans les bases RH et pointage : jamais lues
COLONNES_INTERDITES = re.compile(
    r"\b(fullname|emp_firstname|emp_lastname|emp_ssn|nationalID|emp_pin|emp_phone|emp_birthday|"
    r"emp_hourlyrate\d|emp_address|emp_email|tele|email|NOM|PRENOM|TELEPHONE|codex3|"
    r"CHEMIN_CV|bank_account\w*)\b",
    re.IGNORECASE,
)


def test_les_requetes_ne_lisent_aucune_colonne_personnelle():
    for agregat in AGREGATS:
        assert not COLONNES_INTERDITES.search(agregat.requete), agregat.nom


def test_les_requetes_sont_des_agregations():
    for agregat in AGREGATS:
        assert "GROUP BY" in agregat.requete.upper(), agregat.nom
        assert "personnes" in agregat.sommes, agregat.nom
        assert agregat.groupe in agregat.cles, agregat.nom
