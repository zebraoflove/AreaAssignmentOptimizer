"""
Импорт стран мира в базу данных.
"""

import csv

from src.common.config import ROOT_DIR
from src.common.database import connect


COUNTRIES_FILE = (
    ROOT_DIR
    / "data"
    / "source"
    / "countries"
    / "countries.csv"
)


def read_countries():
    """Читает страны из CSV-файла."""
    with COUNTRIES_FILE.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        reader = csv.DictReader(file)
        return list(reader)


def validate_countries(rows):
    """Проверяет корректность данных."""
    required = {
        "name",
        "iso2",
        "iso3",
        "region",
        "area_sq_km",
    }

    if not rows:
        raise ValueError("countries.csv is empty.")

    missing = required - set(rows[0].keys())

    if missing:
        raise ValueError(
            f"Missing columns: {', '.join(sorted(missing))}"
        )

    names = set()
    valid_rows = []

    for row in rows:
        name = row["name"].strip()

        if not name:
            raise ValueError("Empty country name.")

        if name in names:
            raise ValueError(
                f"Duplicate country: {name}"
            )

        names.add(name)

        area_text = row["area_sq_km"].strip()

        if not area_text:
            continue

        area = float(area_text)

        if area <= 0:
            continue

        valid_rows.append(row)

    print(
        f"Validated {len(valid_rows)} countries."
    )

    return valid_rows


def clear_countries_table(conn):
    """Очищает таблицу countries_raw."""
    conn.execute(
        "DELETE FROM countries_raw"
    )


def insert_countries(conn, rows):
    """Добавляет страны в базу."""
    polar_territories = {
        "Bouvet Island",
        "Heard Island and McDonald Islands",
    }

    conn.executemany(
        """
        INSERT INTO countries_raw (
            name,
            iso_alpha2,
            iso_alpha3,
            continent,
            area_km2
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                row["name"].strip(),
                row["iso2"].strip(),
                row["iso3"].strip(),
                (
                    "Polar"
                    if row["name"].strip()
                    in polar_territories
                    else row["region"].strip()
                ),
                float(row["area_sq_km"]),
            )
            for row in rows
        ],
    )


def import_countries(conn):
    """Импортирует страны в countries_raw."""
    rows = read_countries()
    rows = validate_countries(rows)

    clear_countries_table(conn)
    insert_countries(conn, rows)

    return len(rows)


def main():
    conn = connect()

    try:
        count = import_countries(conn)
        conn.commit()
        print(
            f"Imported {count} countries."
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()