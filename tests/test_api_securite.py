"""Sécurité de l'API : tentatives de connexion, jetons, périmètre, en-têtes, documentation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from api.config import ParametresApi
from api.limites import LimiteurTentatives
from api.main import creer_app
from api.roles import ROLES
from tests.test_api import CLE, MOT_DE_PASSE, FauxEntrepot


def _parametres(**reglages) -> ParametresApi:
    return ParametresApi(_env_file=None, api_db_password="x", api_secret_key=CLE, **reglages)


def _entrepot() -> FauxEntrepot:
    faux = FauxEntrepot()
    for role in ROLES:
        faux.ajouter(
            f"compte.{role}", role, representant="R012" if role == "representant" else None
        )
    return faux


@pytest.fixture
def entrepot() -> FauxEntrepot:
    return _entrepot()


@pytest.fixture
def client(entrepot) -> TestClient:
    # Une application neuve par test : les compteurs de tentatives repartent de zéro
    return TestClient(creer_app(_parametres(), entrepot))


def _connexion(client, identifiant, mot_de_passe=MOT_DE_PASSE):
    return client.post("/v1/auth/jeton", data={"username": identifiant, "password": mot_de_passe})


# ─── Tentatives de connexion ─────────────────────────────────────────


def test_cinq_echecs_bloquent_le_compte(client):
    for _ in range(5):
        assert _connexion(client, "compte.direction", "faux").status_code == 401
    bloque = _connexion(client, "compte.direction")  # même le BON mot de passe
    assert bloque.status_code == 429
    assert int(bloque.headers["Retry-After"]) > 0


def test_le_blocage_d_un_compte_ne_touche_pas_les_autres(client):
    for _ in range(5):
        _connexion(client, "compte.direction", "faux")
    assert _connexion(client, "compte.rh").status_code == 200


def test_une_connexion_reussie_remet_le_compteur_a_zero(client):
    for _ in range(4):
        _connexion(client, "compte.direction", "faux")
    assert _connexion(client, "compte.direction").status_code == 200
    for _ in range(4):
        _connexion(client, "compte.direction", "faux")
    assert _connexion(client, "compte.direction").status_code == 200


def test_une_adresse_qui_essaie_tous_les_comptes_est_bloquee(entrepot):
    client = TestClient(creer_app(_parametres(api_tentatives_par_adresse=6), entrepot))
    for i in range(6):
        _connexion(client, f"compte.inconnu{i}", "faux")
    assert _connexion(client, "compte.direction").status_code == 429


def test_le_blocage_se_leve_apres_la_fenetre():
    maintenant = [1000.0]
    limiteur = LimiteurTentatives(2, 100, fenetre_secondes=900, horloge=lambda: maintenant[0])
    limiteur.echec("a", "ip")
    limiteur.echec("a", "ip")
    assert limiteur.attente("a", "ip") == 901 - 0  # 900 s restantes, arrondi au-dessus
    maintenant[0] += 900
    assert limiteur.attente("a", "ip") == 0


# ─── Jetons ──────────────────────────────────────────────────────────


def _jeton(**contenu) -> str:
    maintenant = datetime.now(UTC)
    base = {
        "sub": "compte.direction",
        "iat": maintenant,
        "exp": maintenant + timedelta(hours=1),
        "iss": "jbel-annour-analytix",
        "aud": "analytix-api",
    }
    base.update(contenu)
    return jwt.encode({k: v for k, v in base.items() if v is not None}, CLE, "HS256")


@pytest.mark.parametrize(
    "contenu",
    [
        {"aud": "une-autre-application"},
        {"iss": "un-autre-emetteur"},
        {"aud": None},
        {"iss": None},
    ],
)
def test_jeton_d_une_autre_application_refuse(client, contenu):
    entete = {"Authorization": f"Bearer {_jeton(**contenu)}"}
    assert client.get("/v1/auth/moi", headers=entete).status_code == 401


def test_jeton_valide_accepte(client):
    entete = {"Authorization": f"Bearer {_jeton()}"}
    assert client.get("/v1/auth/moi", headers=entete).status_code == 200


# ─── Périmètre transmis à PostgreSQL (sécurité par ligne) ─────────────


def _entete(client, identifiant):
    return {"Authorization": f"Bearer {_connexion(client, identifiant).json()['access_token']}"}


@pytest.mark.parametrize(
    ("identifiant", "attendu"),
    [("compte.representant", "R012"), ("compte.commercial", "*"), ("compte.direction", "*")],
)
def test_chaque_lecture_declare_le_perimetre(client, entrepot, identifiant, attendu):
    entete = _entete(client, identifiant)
    entrepot.perimetres.clear()
    assert client.get("/v1/ventes/ca-mensuel", headers=entete).status_code == 200
    # Toutes les lectures de la requête, y compris celle du compte, portent le périmètre
    lectures_donnees = [
        p
        for (sql, _), p in zip(
            entrepot.requetes[-len(entrepot.perimetres) :], entrepot.perimetres, strict=True
        )
        if "marts." in sql
    ]
    assert lectures_donnees == [attendu]


def test_sans_utilisateur_le_perimetre_est_vide(client, entrepot):
    """Santé et connexion lisent sans périmètre : les tables protégées n'y montreraient rien."""
    entrepot.perimetres.clear()
    client.get("/v1/sante")
    assert entrepot.perimetres == [""]


# ─── En-têtes et documentation ───────────────────────────────────────


def test_en_tetes_de_securite(client):
    reponse = client.get("/v1/sante")
    assert reponse.headers["X-Content-Type-Options"] == "nosniff"
    assert reponse.headers["X-Frame-Options"] == "DENY"
    assert reponse.headers["Referrer-Policy"] == "no-referrer"
    assert reponse.headers["Cache-Control"] == "no-store"
    assert "default-src 'none'" in reponse.headers["Content-Security-Policy"]


def test_documentation_ouverte_en_dev(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    # La page /docs charge l'interface Swagger : pas de CSP qui la bloquerait
    assert "Content-Security-Policy" not in client.get("/docs").headers


def test_documentation_fermee_en_prod(entrepot):
    client = TestClient(creer_app(_parametres(analytix_env="prod"), entrepot))
    for chemin in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(chemin).status_code == 404, chemin


def test_documentation_rouverte_en_prod_si_demande(entrepot):
    client = TestClient(creer_app(_parametres(analytix_env="prod", api_docs=True), entrepot))
    assert client.get("/docs").status_code == 200
