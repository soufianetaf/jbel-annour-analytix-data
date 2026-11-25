"""Configuration de l'ingestion, lue dans le fichier .env.

Chaque source SQL Server a ses variables, avec un préfixe :

    X3_…      Sage X3, dossier BASE1
    JBELRH_…  Sage X3, dossier du groupe (données RH sensibles)
    USINE_…   serveur des applications de l'usine

Les mots de passe sont des ``SecretStr`` : ils ne s'affichent jamais,
ni dans un ``print``, ni dans un message d'erreur, ni dans les journaux.

Ce module ne concerne que l'ingestion. L'API aura sa propre
configuration, sans aucun accès aux sources.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Le .env est cherché à la racine du dépôt, quel que soit le dossier
# depuis lequel on lance la commande.
FICHIER_ENV = Path(__file__).resolve().parents[1] / ".env"


def _config(prefixe: str = "") -> SettingsConfigDict:
    return SettingsConfigDict(
        env_prefix=prefixe,
        env_file=FICHIER_ENV,
        env_file_encoding="utf-8",
        extra="ignore",  # le .env contient aussi les variables des autres sources
        env_ignore_empty=True,  # « X3_PORT= » vaut « non renseigné »
    )


class Parametres(BaseSettings):
    """Paramètres communs à toutes les sources."""

    model_config = _config()

    analytix_env: Literal["dev", "prod"] = "dev"
    odbc_driver: str = "ODBC Driver 18 for SQL Server"
    # « yes » seulement si le serveur interne utilise un certificat auto-signé
    sqlserver_trust_cert: bool = False


class SourceSqlServer(BaseSettings):
    """Une source SQL Server, lue avec un compte en lecture seule."""

    model_config = _config()

    # Adresse du serveur, éventuellement avec l'instance : serveur\\INSTANCE
    host: str | None = None
    port: int | None = None
    # Base par défaut ; une source peut contenir plusieurs bases (usine)
    database: str | None = None
    # sql : compte et mot de passe SQL Server ; windows : compte Windows du poste
    auth: Literal["sql", "windows"] = "sql"
    user: str | None = None
    password: SecretStr | None = None

    @property
    def configuree(self) -> bool:
        """Vrai si la source est renseignée dans le .env."""
        return bool(self.host)

    @model_validator(mode="after")
    def _verifier_identifiants(self) -> SourceSqlServer:
        if self.configuree and self.auth == "sql" and not (self.user and self.password):
            raise ValueError("authentification « sql » : le compte et le mot de passe sont requis")
        return self


class SourceX3(SourceSqlServer):
    """Sage X3, dossier BASE1 : gestion de Jbel Annour."""

    model_config = _config("X3_")

    # Dossier X3 (variable X3_DOSSIER) : dans Sage X3, chaque dossier est
    # un schéma SQL. Seul BASE1 est le dossier réel de Jbel Annour.
    dossier: str = "BASE1"


class SourceJbelrh(SourceSqlServer):
    """Sage X3, dossier du groupe : 7 sociétés, pointage, paie."""

    model_config = _config("JBELRH_")


class SourceUsine(SourceSqlServer):
    """Serveur des applications de l'usine (machines, production, maintenance…)."""

    model_config = _config("USINE_")


@lru_cache
def parametres() -> Parametres:
    return Parametres()


@lru_cache
def sources() -> dict[str, SourceSqlServer]:
    """Toutes les sources, par nom court."""
    return {
        "x3": SourceX3(),
        "jbelrh": SourceJbelrh(),
        "usine": SourceUsine(),
    }
