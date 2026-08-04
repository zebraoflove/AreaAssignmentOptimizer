"""
Подготовка данных субъектов Российской Федерации.
"""


from src.common.database import connect

import re

def read_raw_subjects(conn):
    """Читает субъекты из subjects_raw."""

    return conn.execute(
        """
        SELECT
            name,
            type,
            federal_district,
            area_km2
        FROM subjects_raw
        ORDER BY name
        """
    ).fetchall()

def clear_final_table(conn):
    """Очищает subjects_final."""

    conn.execute(
        "DELETE FROM subjects_final"
    )


def normalize_subject(row):
    """Нормализует данные субъекта РФ."""

    row = dict(row)

    row["name"] = re.sub(
        r"\s+",
        " ",
        row["name"].strip(),
    )

    row["type"] = row["type"].strip()

    row["federal_district"] = re.sub(
        r"\s+",
        " ",
        row["federal_district"].strip(),
    )

    return row


def validate_subject(row):
    """Проверяет корректность субъекта РФ."""

    if not row["name"]:
        raise ValueError("Subject name is empty")

    if not row["type"]:
        raise ValueError(
            f"Missing type: {row['name']}"
        )

    if not row["federal_district"]:
        raise ValueError(
            f"Missing district: {row['name']}"
        )

    if row["area_km2"] <= 0:
        raise ValueError(
            f"Invalid area for {row['name']}: {row['area_km2']}"
        )

    return row


def validate_unique(rows):
    """Проверяет уникальность субъектов РФ."""

    names = set()

    for row in rows:

        if row["name"] in names:
            raise ValueError(
                f"Duplicate subject: {row['name']}"
            )

        names.add(row["name"])


def prepare_subjects():
    """Подготавливает таблицу subjects_final."""

    conn = connect()

    try:

        rows = [
            validate_subject(normalize_subject(row))
            for row in read_raw_subjects(conn)
        ]

        validate_unique(rows)
        
        clear_final_table(conn)

        insert_final_subjects(conn, rows)

        conn.commit()

    finally:

        conn.close()

    print(f"Prepared {len(rows)} subjects.")


def insert_final_subjects(conn, rows):
    """Записывает субъекты в subjects_final."""

    conn.executemany(
        """
        INSERT INTO subjects_final (
            name,
            type,
            federal_district,
            area_km2
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                row["name"],
                row["type"],
                row["federal_district"],
                row["area_km2"],
            )
            for row in rows
        ],
    )


def main():
    prepare_subjects()


if __name__ == "__main__":
    main()