"""Tests de la connexion SQL Server (ingestion/sqlserver.py), sans serveur."""

import pytest
from pydantic import SecretStr

from ingestion.config import Parametres, SourceUsine, SourceX3
from ingestion.sqlserver import chaine_connexion, droits_interdits

PARAMS = Parametres(_env_file=None)


def _elements(chaine: str) -> dict[str, str]:
    """Découpe une chaîne de connexion simple (sans « ; » dans les valeurs)."""
    return dict(element.split("=", 1) for element in chaine.split(";"))


def _source_x3(**valeurs: object) -> SourceX3:
    base = {"host": "serveur", "user": "lecteur", "password": SecretStr("secret")}
    return SourceX3(_env_file=None, **(base | valeurs))


# ─── Chaîne de connexion ────────────────────────────────────────────


def test_connexion_en_lecture_seule_et_identifiee() -> None:
    elements = _elements(chaine_connexion(_source_x3(), PARAMS))

    assert elements["ApplicationIntent"] == "ReadOnly"
    assert elements["APP"] == "Jbel Annour Analytix"
    assert elements["Encrypt"] == "yes"
    assert elements["TrustServerCertificate"] == "no"


def test_pilote_entre_accolades() -> None:
    elements = _elements(chaine_connexion(_source_x3(), PARAMS))

    assert elements["DRIVER"] == "{ODBC Driver 18 for SQL Server}"


def test_port_ajoute_au_serveur() -> None:
    elements = _elements(chaine_connexion(_source_x3(port=1433), PARAMS))

    assert elements["SERVER"] == "serveur,1433"


def test_instance_nommee_sans_port() -> None:
    elements = _elements(chaine_connexion(_source_x3(host="serveur\\ERPX3"), PARAMS))

    assert elements["SERVER"] == "serveur\\ERPX3"


def test_base_choisie_remplace_la_base_par_defaut() -> None:
    source = _source_x3(database="x3")

    assert _elements(chaine_connexion(source, PARAMS))["DATABASE"] == "x3"
    assert _elements(chaine_connexion(source, PARAMS, database="moulage"))["DATABASE"] == "moulage"


def test_authentification_windows_sans_mot_de_passe() -> None:
    source = SourceUsine(_env_file=None, host="serveur", auth="windows")

    elements = _elements(chaine_connexion(source, PARAMS))

    assert elements["Trusted_Connection"] == "yes"
    assert "UID" not in elements
    assert "PWD" not in elements


@pytest.mark.parametrize(
    ("mot_de_passe", "attendu"),
    [
        ("simple", "PWD=simple"),
        ("avec;point-virgule", "PWD={avec;point-virgule}"),
        ("avec}accolade", "PWD={avec}}accolade}"),
        ("a=b", "PWD={a=b}"),
        (" espace", "PWD={ espace}"),
    ],
)
def test_mot_de_passe_protege(mot_de_passe: str, attendu: str) -> None:
    # Sans protection, un « ; » dans le mot de passe couperait la chaîne
    # et le reste serait lu comme un autre paramètre.
    chaine = chaine_connexion(_source_x3(password=SecretStr(mot_de_passe)), PARAMS)

    assert attendu in chaine


def test_source_non_configuree_refusee() -> None:
    with pytest.raises(ValueError, match="non configurée"):
        chaine_connexion(SourceUsine(_env_file=None), PARAMS)


# ─── Contrôle des droits ────────────────────────────────────────────

LECTURE_SEULE = {
    "compte": "analytix_lecteur",
    "sysadmin": 0,
    "control_server": 0,
    "db_owner": 0,
    "db_datawriter": 0,
    "db_ddladmin": 0,
    "peut_inserer": 0,
    "peut_modifier": 0,
    "peut_supprimer": 0,
    "peut_alterer": 0,
}


def test_compte_lecture_seule_accepte() -> None:
    assert droits_interdits(LECTURE_SEULE) == []


def test_compte_sa_refuse() -> None:
    droits = LECTURE_SEULE | {"sysadmin": 1, "control_server": 1, "db_owner": 1}

    problemes = droits_interdits(droits)

    assert len(problemes) == 3
    assert any("sysadmin" in probleme for probleme in problemes)


@pytest.mark.parametrize(
    "droit",
    ["db_datawriter", "db_ddladmin", "peut_inserer", "peut_modifier", "peut_supprimer"],
)
def test_tout_droit_d_ecriture_refuse(droit: str) -> None:
    assert len(droits_interdits(LECTURE_SEULE | {droit: 1})) == 1


def test_droit_d_ecriture_sur_le_dossier_x3_refuse() -> None:
    # Un compte peut écrire dans BASE1 sans être membre d'aucun rôle
    droits = LECTURE_SEULE | {"schemas": {"BASE1": {"SELECT": 1, "INSERT": 1, "UPDATE": 0}}}

    assert droits_interdits(droits) == ["droit INSERT sur le schéma BASE1"]


def test_dossier_x3_en_lecture_seule_accepte() -> None:
    droits = LECTURE_SEULE | {"schemas": {"BASE1": {"INSERT": 0, "UPDATE": 0, "ALTER": 0}}}

    assert droits_interdits(droits) == []


def test_droit_inconnu_du_serveur_non_bloquant() -> None:
    # IS_ROLEMEMBER renvoie NULL (None) si le rôle n'existe pas : pas un droit
    assert droits_interdits(LECTURE_SEULE | {"db_ddladmin": None}) == []
