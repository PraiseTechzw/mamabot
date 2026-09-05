"""MySQL connection helpers with clear local failure behavior."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

try:
    import mysql.connector
except ImportError:  # pragma: no cover - exercised only in minimal local installs
    mysql = None  # type: ignore[assignment]
from config import settings

log = logging.getLogger(__name__)


class DatabaseConnectionError(RuntimeError):
    """Raised when MySQL cannot be reached or a connection cannot be used."""


@contextmanager
def get_connection() -> Generator[object, None, None]:
    if mysql is None:
        raise DatabaseConnectionError("mysql-connector-python is not installed")
    try:
        connection = mysql.connector.connect(**settings.mysql_config)
    except Exception as exc:  # connector exposes several version-specific errors
        log.warning("Unable to connect to MySQL: %s", exc)
        raise DatabaseConnectionError(
            "Unable to connect to the configured database"
        ) from exc
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def get_cursor(dictionary: bool = True) -> Generator[object, None, None]:
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=dictionary)
        try:
            yield cursor
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
