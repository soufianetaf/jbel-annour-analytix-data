"""API : connexion, droits par rôle, filtre du représentant, journal des accès.

Un faux entrepôt remplace PostgreSQL : il renvoie les comptes de test et
garde les requêtes reçues, pour vérifier les filtres. Exigence du cahier des
charges : un utilisateur ne peut obtenir aucune donnée hors de son rôle
(tests d'accès pour chaque rôle).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from api.config import ParametresApi
from api.main import ROUTEURS, VERSION, creer_app
from api.roles import DOMAINES, ROLES
from api.securite import empreinte

MOT_DE_PASSE = "un-mot-de-passe-de-test"
CLE = "cle-de-test-" + "x" * 40


class FauxEntrepot:
    def __init__(self) -> None:
        self.comptes: dict[str, dict] = {}
        self.requetes: list[tuple[str, dict | None]] = []
        self.perimetres: list[str] = []

    def ajouter(self, identifiant: str, role: str, representant: str | None = None, actif=True):
        self.comptes[identifiant] = {
            "identifiant": identifiant,
            "empreinte_mot_de_passe": empreinte(MOT_DE_PASSE),
            "role": role,
            "representant": representant,
            "actif": actif,
        }

    def lire(self, sql: str, parametres: dict | None = None, perimetre: str = "") -> list[dict]:
        self.requetes.append((sql, parametres))
        self.perimetres.append(perimetre)
        if "FROM api.utilisateurs" in sql:
            compte = self.comptes.get(parametres["identifiant"])
            return [compte] if compte else []
        return []


@pytest.fixture(scope="module")
def parametres() -> ParametresApi:
    return ParametresApi(_env_file=None, api_db_password="x", api_secret_key=CLE)


@pytest.fixture(scope="module")
def entrepot() -> FauxEntrepot:
    faux = FauxEntrepot()
    for role in ROLES:
        faux.ajouter(
            f"compte.{role}", role, representant="R012" if role == "representant" else None
        )
    faux.ajouter("representant.sans.code", "representant")
    faux.ajouter("compte.desactive", "direction", actif=False)
    return faux


@pytest.fixture(scope="module")
def client(parametres, entrepot) -> TestClient:
    return TestClient(creer_app(parametres, entrepot))


def _jeton(client: TestClient, identifiant: str, mot_de_passe: str = MOT_DE_PASSE):
    return client.post("/v1/auth/jeton", data={"username": identifiant, "password": mot_de_passe})


def _entete(client: TestClient, identifiant: str) -> dict[str, str]:
    reponse = _jeton(client, identifiant)
    assert reponse.status_code == 200, reponse.text
    return {"Authorization": f"Bearer {reponse.json()['access_token']}"}


def _routes_get() -> list[APIRoute]:
    """Chaque route GET de l'API, prise dans la liste des routeurs (api/main.py).

    Pas dans app.routes : depuis FastAPI 0.16x, les routes incluses y sont
    rangées dans des objets internes, et le test passait sans en voir aucune.
    test_les_routes_testees_sont_celles_publiees le vérifie.
    """
    return [
        route
        for module in ROUTEURS
        for route in module.routeur.routes
        if isinstance(route, APIRoute) and "GET" in route.methods
    ]


def _routes_protegees(client: TestClient | None = None) -> list[tuple[str, str]]:
    """(chemin complet, domaine) de chaque route GET qui déclare un domaine."""
    routes = []
    for route in _routes_get():
        domaines = [getattr(d.call, "domaine", None) for d in route.dependant.dependencies]
        domaines = [d for d in domaines if d]
        if domaines:
            routes.append((f"/{VERSION}{route.path}", domaines[0]))
    return routes


# ─── Connexion ───────────────────────────────────────────────────────


def test_sante_sans_connexion(client):
    reponse = client.get("/v1/sante")
    assert reponse.status_code == 200
    assert reponse.json()["api"] == "ok"


def test_sante_donne_le_dernier_chargement():
    """L'heure renvoyée est la copie la moins récente, lue hors des tables à sécurité par ligne."""
    from api.routes.sante import SQL_DERNIER_CHARGEMENT, sante

    class EntrepotChargement:
        def __init__(self, lignes):
            self.lignes, self.sql = lignes, []

        def lire(self, sql, parametres=None, perimetre=""):
            self.sql.append(sql)
            return self.lignes

    heure = datetime(2026, 11, 27, 14, 0, tzinfo=UTC)
    faux = EntrepotChargement([{"dernier_chargement": heure}])
    reponse = sante(faux)
    assert reponse.entrepot == "ok"
    assert reponse.dernier_chargement == heure
    assert faux.sql == [SQL_DERNIER_CHARGEMENT]
    for protegee in ("fct_ventes", "fct_livraisons", "fct_commandes"):
        assert protegee not in SQL_DERNIER_CHARGEMENT
    assert "min(dernier)" in SQL_DERNIER_CHARGEMENT

    assert sante(EntrepotChargement([])).dernier_chargement is None


def test_sante_entrepot_indisponible():
    from api.routes.sante import sante

    class EntrepotEnPanne:
        def lire(self, sql, parametres=None, perimetre=""):
            raise ConnectionError("injoignable")

    reponse = sante(EntrepotEnPanne())
    assert reponse.entrepot == "indisponible"
    assert reponse.dernier_chargement is None


def test_connexion_avec_le_bon_mot_de_passe(client):
    reponse = _jeton(client, "compte.direction")
    assert reponse.status_code == 200
    assert reponse.json()["token_type"] == "bearer"


@pytest.mark.parametrize(
    ("identifiant", "mot_de_passe"),
    [
        ("compte.direction", "mauvais-mot-de-passe"),
        ("compte.inconnu", MOT_DE_PASSE),
        ("compte.desactive", MOT_DE_PASSE),
    ],
)
def test_connexion_refusee(client, identifiant, mot_de_passe):
    reponse = _jeton(client, identifiant, mot_de_passe)
    assert reponse.status_code == 401
    # Même message dans tous les cas : on ne devine pas quels comptes existent
    assert reponse.json()["detail"] == "Identifiant ou mot de passe incorrect"


def test_moi_donne_le_role_et_les_domaines(client):
    reponse = client.get("/v1/auth/moi", headers=_entete(client, "compte.rh"))
    assert reponse.json() == {
        "identifiant": "compte.rh",
        "role": "rh",
        "domaines": ["qualite_donnees", "rh"],
    }


def test_jeton_expire_refuse(client, parametres):
    passe = datetime.now(UTC) - timedelta(hours=10)
    jeton = jwt.encode(
        {"sub": "compte.direction", "iat": passe, "exp": passe + timedelta(hours=8)},
        CLE,
        "HS256",
    )
    reponse = client.get("/v1/auth/moi", headers={"Authorization": f"Bearer {jeton}"})
    assert reponse.status_code == 401


def test_jeton_signe_par_une_autre_cle_refuse(client):
    maintenant = datetime.now(UTC)
    jeton = jwt.encode(
        {"sub": "compte.direction", "iat": maintenant, "exp": maintenant + timedelta(hours=1)},
        "une-autre-cle-" + "y" * 40,
        "HS256",
    )
    reponse = client.get("/v1/auth/moi", headers={"Authorization": f"Bearer {jeton}"})
    assert reponse.status_code == 401


def test_compte_desactive_apres_connexion_perd_ses_droits(client, entrepot):
    entrepot.ajouter("compte.temporaire", "direction")
    entete = _entete(client, "compte.temporaire")
    assert client.get("/v1/auth/moi", headers=entete).status_code == 200
    entrepot.comptes["compte.temporaire"]["actif"] = False
    assert client.get("/v1/auth/moi", headers=entete).status_code == 401


def test_cle_trop_courte_refusee():
    with pytest.raises(ValueError, match="API_SECRET_KEY trop courte"):
        ParametresApi(_env_file=None, api_db_password="x", api_secret_key="courte")


# ─── Droits par rôle ─────────────────────────────────────────────────


def test_toutes_les_routes_de_donnees_declarent_un_domaine(client):
    """Toute route GET, sauf /sante et /auth/moi, doit être réservée à un domaine."""
    libres = {"/v1/sante", "/v1/auth/moi"}
    protegees = {chemin for chemin, _ in _routes_protegees(client)}
    for route in _routes_get():
        chemin = f"/{VERSION}{route.path}"
        assert chemin in protegees | libres, f"{chemin} sans domaine"


def test_les_routes_testees_sont_celles_publiees(client):
    """Les routes vérifiées ici sont exactement celles que l'API publie (OpenAPI).

    Garde-fou : une route publiée hors de la liste des routeurs échapperait
    à la matrice des droits ; et une matrice vide passerait sans rien tester.
    """
    publiees = {
        chemin for chemin, methodes in client.app.openapi()["paths"].items() if "get" in methodes
    }
    testees = {f"/{VERSION}{route.path}" for route in _routes_get()}
    assert testees == publiees
    # 32 routes de données au 26/11/2026 : à relever quand on en ajoute
    assert len(_routes_protegees(client)) >= 34


def test_toutes_les_routes_de_donnees_exigent_une_connexion(client):
    for chemin, _ in _routes_protegees(client):
        assert client.get(chemin).status_code == 401, chemin


def test_chaque_domaine_utilise_existe(client):
    for chemin, domaine in _routes_protegees(client):
        assert domaine in DOMAINES, f"{chemin} : domaine « {domaine} » absent de api/roles.py"


@pytest.mark.parametrize("role", ROLES)
def test_matrice_des_droits(client, role):
    """Chaque rôle : 200 sur ses domaines, 403 sur tous les autres."""
    entete = _entete(client, f"compte.{role}")
    for chemin, domaine in _routes_protegees(client):
        attendu = 200 if role in DOMAINES[domaine] else 403
        assert client.get(chemin, headers=entete).status_code == attendu, (role, chemin)


def test_rh_fermee_au_commercial_et_a_la_finance(client):
    for role in ("commercial", "finance", "administrateur", "representant"):
        entete = _entete(client, f"compte.{role}")
        assert client.get("/v1/rh/effectifs", headers=entete).status_code == 403, role


def test_administrateur_ne_voit_aucune_donnee_metier(client):
    entete = _entete(client, "compte.administrateur")
    for chemin in ("/v1/ventes/ca-mensuel", "/v1/direction/mois", "/v1/rh/effectifs"):
        assert client.get(chemin, headers=entete).status_code == 403, chemin


# ─── Filtre du représentant ──────────────────────────────────────────


def test_representant_filtre_sur_son_code(client, entrepot):
    entete = _entete(client, "compte.representant")
    entrepot.requetes.clear()
    assert client.get("/v1/ventes/ca-mensuel", headers=entete).status_code == 200
    sql, parametres = entrepot.requetes[-1]
    assert "representant = %(representant)s" in sql
    assert parametres["representant"] == "R012"


def test_representant_filtre_sur_les_livraisons(client, entrepot):
    entete = _entete(client, "compte.representant")
    for chemin in (
        "/v1/ventes/cycle-mois",
        "/v1/ventes/livre-non-facture",
        "/v1/ventes/livre-non-facture/resume",
    ):
        assert client.get(chemin, headers=entete).status_code == 200, chemin
        sql, parametres = entrepot.requetes[-1]
        assert "representant = %(representant)s" in sql, chemin
        assert parametres["representant"] == "R012", chemin


def test_commercial_voit_tous_les_representants(client, entrepot):
    entete = _entete(client, "compte.commercial")
    client.get("/v1/ventes/clients", headers=entete)
    _, parametres = entrepot.requetes[-1]
    assert parametres["representant"] is None


def test_representant_sans_code_ne_voit_rien(client):
    entete = _entete(client, "representant.sans.code")
    assert client.get("/v1/ventes/ca-mensuel", headers=entete).status_code == 403


# ─── Paramètres et journal ───────────────────────────────────────────


def test_periode_inversee_refusee(client):
    entete = _entete(client, "compte.direction")
    reponse = client.get(
        "/v1/direction/mois", params={"debut": "2026-06-01", "fin": "2026-01-01"}, headers=entete
    )
    assert reponse.status_code == 422


def test_journal_des_acces(client, caplog):
    entete = _entete(client, "compte.direction")
    with caplog.at_level(logging.INFO, logger="analytix.acces"):
        client.get("/v1/direction/mois", params={"debut": "2026-01-01"}, headers=entete)
    ligne = json.loads(caplog.records[-1].getMessage())
    assert ligne["utilisateur"] == "compte.direction"
    assert ligne["role"] == "direction"
    assert ligne["chemin"] == "/v1/direction/mois"
    assert ligne["filtres"] == {"debut": "2026-01-01"}
    assert ligne["statut"] == 200


def test_journal_sans_mot_de_passe_ni_jeton(client, caplog):
    with caplog.at_level(logging.INFO, logger="analytix.acces"):
        _jeton(client, "compte.direction")
    texte = caplog.records[-1].getMessage()
    assert MOT_DE_PASSE not in texte
    assert "Bearer" not in texte


def test_roles_identiques_api_et_entrepot():
    from infra.postgres.initialiser_entrepot import ROLES_APPLICATIFS

    assert ROLES == ROLES_APPLICATIFS
