"""
AreaAssignmentOptimizer

Единая конфигурация проекта.

Все остальные модули получают пути только отсюда.
"""

from pathlib import Path


# ----------------------------------------------------------
# Корневая директория проекта
# ----------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]


# ----------------------------------------------------------
# Каталоги проекта
# ----------------------------------------------------------

DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

DATABASE_DIR = ROOT_DIR / "database"
EXPORT_DIR = ROOT_DIR / "exports"
OUTPUT_DIR = ROOT_DIR / "output"
LOGS_DIR = ROOT_DIR / "logs"
ROSSTAT_2025_DIR = ROOT_DIR / "data" / "source" / "rosstat" / "regions_2025"


# ----------------------------------------------------------
# Файлы
# ----------------------------------------------------------

DATABASE_PATH = DATABASE_DIR / "world.db"

COUNTRIES_RAW_PATH = RAW_DATA_DIR / "countries_raw.csv"
SUBJECTS_PATH = RAW_DATA_DIR / "subjects_raw.csv"
ADJUSTMENTS_PATH = RAW_DATA_DIR / "territory_adjustments.csv"


# ----------------------------------------------------------
# Создание необходимых каталогов
# ----------------------------------------------------------

for directory in (
    DATABASE_DIR,
    EXPORT_DIR,
    OUTPUT_DIR,
    LOGS_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)