"""Initialize a configured MySQL database with schema, indexes, and seed data."""

from pathlib import Path

from database.connection import get_connection

ROOT = Path(__file__).resolve().parents[1]


def _statements(path: Path) -> list[str]:
    return [
        statement.strip()
        for statement in path.read_text(encoding="utf-8").split(";")
        if statement.strip()
    ]


def initialize_database() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        try:
            for filename in ("schema.sql", "indexes.sql", "seed.sql"):
                for statement in _statements(ROOT / "sql" / filename):
                    cursor.execute(statement)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


if __name__ == "__main__":
    initialize_database()
