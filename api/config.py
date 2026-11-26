"""Paramètres de l'API, lus dans .env (jamais écrits dans le code)."""

from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

FICHIER_ENV = Path(__file__).resolve().parents[1] / ".env"
LONGUEUR_MIN_CLE = 32


class ParametresApi(BaseSettings):
    """Variables DW_… (où est l'entrepôt) et API_… du fichier .env."""

    model_config = SettingsConfigDict(
        env_file=FICHIER_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    # Entrepôt : même serveur et même base que l'ingestion et dbt
    dw_host: str = "localhost"
    dw_port: int = 5432
    dw_database: str = "dw_dev"

    # Compte PostgreSQL de l'API : lecture seule forcée par le serveur
    api_db_user: str = "analytix_api"
    api_db_password: SecretStr

    # Clé qui signe les jetons de connexion : longue et aléatoire, propre à
    # chaque environnement (dev, prod)
    api_secret_key: SecretStr
    # Durée d'un jeton : une journée de travail
    api_duree_jeton_minutes: int = 480
    # Adresse(s) de l'interface web autorisée(s) à appeler l'API, séparées par des virgules
    api_cors_origins: str = "http://localhost:5173"

    @field_validator("api_secret_key")
    @classmethod
    def _cle_assez_longue(cls, valeur: SecretStr) -> SecretStr:
        if len(valeur.get_secret_value()) < LONGUEUR_MIN_CLE:
            raise ValueError(
                f"API_SECRET_KEY trop courte : au moins {LONGUEUR_MIN_CLE} caractères "
                "aléatoires (par exemple : uv run python -c "
                '"import secrets; print(secrets.token_urlsafe(48))")'
            )
        return valeur

    @property
    def origines_cors(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]
