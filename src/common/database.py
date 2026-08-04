"""
Работа с базой данных SQLite.
"""

import sqlite3

from src.common.config import DATABASE_PATH


def connect() -> sqlite3.Connection:
    """
    Создаёт подключение к SQLite.
    """

    conn = sqlite3.connect(DATABASE_PATH)

    conn.execute("PRAGMA foreign_keys = ON;")

    conn.row_factory = sqlite3.Row

    return conn