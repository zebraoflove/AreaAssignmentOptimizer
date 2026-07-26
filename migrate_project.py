from pathlib import Path
import shutil

PROJECT = Path("/content/drive/MyDrive/RussiaCountriesProject")
SRC = PROJECT / "src"

print("=" * 60)
print("Project migration")
print("=" * 60)

# --------------------------------------------------
# Создание каталогов
# --------------------------------------------------

for folder in [
    SRC / "common",
    SRC / "importers",
    SRC / "_legacy",
]:
    folder.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Заголовок новых модулей
# --------------------------------------------------

HEADER = '''"""
AreaAssignmentOptimizer

Module:
"""

'''

def ensure_module(path: Path):
    if not path.exists():
        path.write_text(HEADER, encoding="utf-8")
        print(f"[CREATE] {path.relative_to(PROJECT)}")

# --------------------------------------------------
# Создание новых модулей
# --------------------------------------------------

for module in [
    SRC / "common" / "config.py",
    SRC / "common" / "database.py",
    SRC / "common" / "csv_utils.py",

    SRC / "importers" / "import_subjects.py",
    SRC / "importers" / "import_countries.py",
    SRC / "importers" / "import_adjustments.py",

    SRC / "builder.py",
    SRC / "validator.py",
    SRC / "candidate_generator.py",
    SRC / "assignment_solver.py",
    SRC / "local_optimizer.py",
]:
    ensure_module(module)

# --------------------------------------------------
# Перенос старых файлов
# --------------------------------------------------

legacy = [
    "build_subjects.py",
    "candidates.py",
    "loader.py",
    "optimizer.py",
]

for name in legacy:
    src = SRC / name
    dst = SRC / "_legacy" / name

    if src.exists():
        shutil.move(src, dst)
        print(f"[MOVE] {name}")

# --------------------------------------------------
# Проверка обязательных файлов
# --------------------------------------------------

for name in [
    "init_database.py",
    "exporter.py",
    "main.py",
]:
    f = SRC / name

    if f.exists():
        print(f"[ OK ] {name}")
    else:
        print(f"[MISS] {name}")

print("=" * 60)
print("Migration completed.")
print("=" * 60)
