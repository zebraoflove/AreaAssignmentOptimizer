"""
Подготовка данных стран.
"""

from src.common.database import connect

import re


CONTINENT_FIXES = {
    "Bouvet Island": "Antarctica",
    "Heard Island and McDonald Islands": "Antarctica",
}


def read_raw_countries(conn):
    """Читает страны из countries_raw."""

    return conn.execute(
        """
        SELECT
            name,
            iso_alpha2,
            iso_alpha3,
            continent,
            area_km2
        FROM countries_raw
        ORDER BY name
        """
    ).fetchall()


def clear_final_table(conn):
    """Очищает countries_final."""

    conn.execute(
        "DELETE FROM countries_final"
    )


def normalize_country(row):
    """Нормализует данные страны."""

    row = dict(row)

    row["name"] = re.sub(
        r"\s+",
        " ",
        row["name"].strip(),
    )

    continent = row["continent"].strip()

    if not continent:
        continent = CONTINENT_FIXES.get(
            row["name"],
            "",
        )

    row["continent"] = continent

    return row


def validate_country(row):
    """Проверяет корректность данных страны."""

    if not row["name"]:
        raise ValueError("Country name is empty")

    if row["area_km2"] <= 0:
        raise ValueError(
            f"Invalid area for {row['name']}: {row['area_km2']}"
        )

    if not row["continent"]:
        raise ValueError(
            f"Missing continent for {row['name']}"
        )

    return row


def validate_unique(rows):
    """Проверяет уникальность стран."""

    names = set()
    iso2 = set()
    iso3 = set()

    for row in rows:

        if row["name"] in names:
            raise ValueError(
                f"Duplicate country name: {row['name']}"
            )
        names.add(row["name"])

        if row["iso_alpha2"]:

            if row["iso_alpha2"] in iso2:
                raise ValueError(
                    f"Duplicate ISO Alpha-2: {row['iso_alpha2']}"
                )

            iso2.add(row["iso_alpha2"])

        if row["iso_alpha3"]:

            if row["iso_alpha3"] in iso3:
                raise ValueError(
                    f"Duplicate ISO Alpha-3: {row['iso_alpha3']}"
                )

            iso3.add(row["iso_alpha3"])


def prepare_countries():
    """Подготавливает таблицу countries_final."""

    conn = connect()

    try:

        rows = [
            validate_country(
                normalize_country(row)
            )
            for row in read_raw_countries(conn)
        ]

        validate_unique(rows)

        clear_final_table(conn)

        insert_final_countries(conn, rows)

        conn.commit()

    finally:

        conn.close()

    print(f"Prepared {len(rows)} countries.")


def insert_final_countries(conn, rows):
    """Записывает страны в countries_final."""

    conn.executemany(
        """
        INSERT INTO countries_final (
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
                row["name"],
                row["iso_alpha2"],
                row["iso_alpha3"],
                row["continent"],
                row["area_km2"],
            )
            for row in rows
        ],
    )


def main():

    prepare_countries()


if __name__ == "__main__":
    main()