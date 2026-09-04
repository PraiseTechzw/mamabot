"""MySQL connection helpers with clear local failure behavior."""
from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

try:
    import mysql.connector
except ImportError:  # pragma: no cover
    mysql = None
from config import settings

log = logging.getLogger(__name__)

@contextmanager
def get_connection() -> Iterator[object]:
    if "mysql.connector" not in globals() or mysql is None:
        raise RuntimeError("mysql-connector-python is not installed")
    connection = mysql.connector.connect(**settings.mysql_config)
    try:
        yield connection
    finally:
        connection.close()

@contextmanager
def get_cursor(dictionary: bool = True) -> Iterator[object]:
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=dictionary)
        try:
            yield cursor
            connection.commit()
        finally:
            cursor.close()
