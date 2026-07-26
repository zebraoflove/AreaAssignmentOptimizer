"""
AreaAssignmentOptimizer

Создание структуры базы данных SQLite.

Модуль отвечает только за создание схемы базы данных
из SQL-файлов.

SQL хранится отдельно в каталоге database/.
"""

from pathlib import Path
import sqlite3

from src.common.config import DATABASE_PATH, ROOT_DIR


SCHEMA_FILE = ROOT_DIR / "database" / "schema.sql"
INDEXES_FILE = ROOT_DIR / "database" / "indexes.sql"
VIEWS_FILE = ROOT_DIR / "database" / "views.sql"


def connect() -> sqlite3.Connection:
    """Создаёт подключение к SQLite."""

    conn = sqlite3.connect(DATABASE_PATH)

    conn.execute("PRAGMA foreign_keys = ON;")

    conn.row_factory = sqlite3.Row

    return conn


def execute_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    """Выполняет SQL-файл."""

    if not path.exists():
        return

    sql = path.read_text(encoding="utf-8").strip()

    if not sql:
        raise RuntimeError(f"SQL file is empty: {path}")

    if sql:
        conn.executescript(sql)


def create_database() -> None:
    """Создаёт структуру базы данных."""

    conn = connect()

    try:

        execute_sql_file(conn, SCHEMA_FILE)
        
        if INDEXES_FILE.exists():
            execute_sql_file(conn, INDEXES_FILE)
        
        if VIEWS_FILE.exists():
            execute_sql_file(conn, VIEWS_FILE)

        conn.commit()

        print("[OK] Database schema created.")

    finally:

        conn.close()


def main() -> None:
    create_database()


if __name__ == "__main__":
    main()