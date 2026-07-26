"""
AreaAssignmentOptimizer

Создание структуры базы данных SQLite.

Этот модуль отвечает исключительно за:
- создание таблиц;
- создание представлений (VIEW);
- создание индексов;
- включение внешних ключей.

Модуль не импортирует данные.
"""

from pathlib import Path
import sqlite3


# ==========================================================
# Пути
# ==========================================================

PROJECT = Path("/content/drive/MyDrive/RussiaCountriesProject")
DATABASE_DIR = PROJECT / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATABASE_DIR / "world.db"


# ==========================================================
# Подключение
# ==========================================================

def connect() -> sqlite3.Connection:
    """
    Создаёт соединение с SQLite.
    """

    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA foreign_keys = ON;")

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================================
# Выполнение SQL
# ==========================================================

def execute_script(conn: sqlite3.Connection, sql: str) -> None:
    """
    Выполняет SQL-скрипт.
    """

    conn.executescript(sql)


# ==========================================================
# Создание схемы
# ==========================================================

def create_schema(conn: sqlite3.Connection) -> None:

    sql = """
    --------------------------------------------------------------------
    -- Версия схемы
    --------------------------------------------------------------------

    CREATE TABLE IF NOT EXISTS schema_version (

        version INTEGER PRIMARY KEY,

        applied_at TEXT NOT NULL

    );



    --------------------------------------------------------------------
    -- Субъекты Российской Федерации
    --------------------------------------------------------------------

    CREATE TABLE IF NOT EXISTS subjects (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,

        type TEXT NOT NULL,

        federal_district TEXT NOT NULL,

        area_km2 REAL NOT NULL
            CHECK(area_km2 > 0)

    );



    --------------------------------------------------------------------
    -- Государства
    --------------------------------------------------------------------

    CREATE TABLE IF NOT EXISTS countries (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,

        iso_alpha2 TEXT,

        iso_alpha3 TEXT,

        continent TEXT NOT NULL,

        area_km2 REAL NOT NULL
            CHECK(area_km2 > 0)

    );
