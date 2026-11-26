"""Accès à l'entrepôt, en lecture seule.

Trois protections, de la plus forte à la plus faible :
1. le compte analytix_api ne peut rien écrire (droits PostgreSQL, et
   default_transaction_read_only forcé sur le rôle) ;
2. chaque connexion du pool redemande la lecture seule à l'ouverture ;
3. le code ne passe que des requêtes SELECT, avec des paramètres (jamais
   de texte de l'utilisateur collé dans le SQL).
"""

from __future__ import annotations

from typing import Any, Protocol

from api.config import ParametresApi


class Entrepot(Protocol):
    """Ce dont les routes ont besoin : lire des lignes. Remplaçable dans les tests."""

    def lire(self, sql: str, parametres: dict[str, Any] | None = None) -> list[dict[str, Any]]: ...


class EntrepotPostgres:
    """Pool de connexions PostgreSQL avec le compte de l'API."""

    def __init__(self, parametres: ParametresApi) -> None:
        from psycopg.conninfo import make_conninfo
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        conninfo = make_conninfo(
            host=parametres.dw_host,
            port=parametres.dw_port,
            dbname=parametres.dw_database,
            user=parametres.api_db_user,
            password=parametres.api_db_password.get_secret_value(),
            application_name="Jbel Annour Analytix - API",
            connect_timeout=10,
            options="-c default_transaction_read_only=on",
        )
        self._pool = ConnectionPool(
            conninfo,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row, "autocommit": True},
            open=False,
        )

    def ouvrir(self) -> None:
        self._pool.open(wait=False)

    def fermer(self) -> None:
        self._pool.close()

    def lire(self, sql: str, parametres: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._pool.connection() as connexion:
            return connexion.execute(sql, parametres).fetchall()
