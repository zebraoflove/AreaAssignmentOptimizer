from src.common.database import connect

DEBUG = False

def read_subjects(conn):
    """Читает подготовленные субъекты РФ."""

    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT
                id,
                name,
                area_km2
            FROM subjects_final
            ORDER BY id
            """
        ).fetchall()
    ]

def read_countries(conn):
    """Читает подготовленные страны."""

    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT
                id,
                name,
                area_km2
            FROM countries_final
            ORDER BY id
            """
        ).fetchall()
    ]

def generate_candidates(subjects, countries):
    """Генерирует наборы кандидатов для субъектов РФ."""

    candidate_sets = []

    for subject in subjects:

        eligible_countries = [
            country
            for country in countries
            if country["area_km2"]
            <= subject["area_km2"]
        ]

        ranked_countries = sorted(
            eligible_countries,
            key=lambda country: (
                subject["area_km2"]
                - country["area_km2"]
            ),
        )

        candidate_sets.append(
            {
                "subject_id": subject["id"],
                "subject_name": subject["name"],
                "subject_area": subject["area_km2"],
                "countries": [
                    {
                        "country_id": country["id"],
                        "country_name": country["name"],
                        "difference_km2": (
                            subject["area_km2"]
                            - country["area_km2"]
                        ),
                    }
                    for country in ranked_countries
                ],
            }
        )

    return candidate_sets

def clear_candidate_tables(conn):
    """Очищает таблицы candidate_sets."""

    conn.execute("DELETE FROM candidate_set_items")

    conn.execute("DELETE FROM candidate_sets")

def save_candidate_sets(conn, candidate_sets):
    """Сохраняет наборы кандидатов."""

    clear_candidate_tables(conn)

    for candidate_set in candidate_sets:

        cursor = conn.execute(
            """
            INSERT INTO candidate_sets
            (
                subject_id
            )
            VALUES (?)
            """,
            (
                candidate_set["subject_id"],
            ),
        )

        candidate_set_id = cursor.lastrowid

        conn.executemany(
            """
            INSERT INTO candidate_set_items
            (
                candidate_set_id,
                country_id
            )
            VALUES (?, ?)
            """,
            [
                (
                    candidate_set_id,
                    country["country_id"],
                )
                for country in candidate_set["countries"]
            ],
        )

    conn.commit()

def rebuild_candidate_sets(conn):
    """Полностью пересобирает кандидатуры на основе countries_final."""

    subjects = read_subjects(conn)
    countries = read_countries(conn)

    candidate_sets = generate_candidates(
        subjects,
        countries,
    )

    save_candidate_sets(
        conn,
        candidate_sets,
    )

    return len(candidate_sets)

def main():
    conn = connect()

    try:
        count = rebuild_candidate_sets(conn)

        print(
            f"Saved {count} candidate sets."
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()