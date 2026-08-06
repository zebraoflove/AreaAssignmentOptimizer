from src.common.database import connect


def read_candidate_sets(conn):
    """Читает наборы кандидатов."""

    rows = conn.execute(
        """
        SELECT
            cs.id AS candidate_set_id,
            cs.subject_id,
            s.name AS subject_name,

            c.id AS country_id,
            c.name AS country_name

        FROM candidate_sets cs

        JOIN candidate_set_items csi
            ON csi.candidate_set_id = cs.id

        JOIN countries_final c
            ON c.id = csi.country_id

        JOIN subjects_final s
            ON s.id = cs.subject_id

        ORDER BY
            cs.subject_id,
            csi.id
        """
    ).fetchall()

    candidate_sets = {}

    for row in rows:

        subject_id = row["subject_id"]

        if subject_id not in candidate_sets:

            candidate_sets[subject_id] = {
                "subject_id": subject_id,
                "subject_name": row["subject_name"],
                "countries": [],
            }

        candidate_sets[subject_id]["countries"].append(
            {
                "country_id": row["country_id"],
                "country_name": row["country_name"],
            }
        )

    return list(candidate_sets.values())


def generate_assignments(candidate_sets):
    """Формирует окончательные назначения жадным алгоритмом."""

    assignments = []

    used_countries = set()

    for candidate_set in candidate_sets:

        for country in candidate_set["countries"]:

            if country["country_id"] in used_countries:
                continue

            assignments.append(
                {
                    "subject_id": candidate_set["subject_id"],
                    "country_id": country["country_id"],
                }
            )

            used_countries.add(country["country_id"])

            break

    assigned_subjects = {
        assignment["subject_id"]
        for assignment in assignments
    }

    for candidate_set in candidate_sets:

        if candidate_set["subject_id"] not in assigned_subjects:

            if DEBUG:

                print(f"No assignment: {candidate_set['subject_name']}")

                print("Candidate countries:")

                for country in candidate_set["countries"]:
                    print(f"  {country['country_name']}")
    
    return assignments


def clear_assignments(conn):
    """Очищает таблицы assignments."""

    conn.execute(
        "DELETE FROM assignment_items"
    )

    conn.execute(
        "DELETE FROM assignments"
    )


def save_assignments(conn, assignments):
    """Сохраняет окончательные назначения."""

    clear_assignments(conn)

    for assignment in assignments:

        cursor = conn.execute(
            """
            INSERT INTO assignments
            (
                subject_id
            )
            VALUES (?)
            """,
            (
                assignment["subject_id"],
            ),
        )

        assignment_id = cursor.lastrowid

        conn.execute(
            """
            INSERT INTO assignment_items
            (
                assignment_id,
                country_id
            )
            VALUES (?, ?)
            """,
            (
                assignment_id,
                assignment["country_id"],
            ),
        )

    conn.commit()

    print(
        f"Saved {len(assignments)} assignments."
    )


def main():

    conn = connect()

    try:

        candidate_sets = read_candidate_sets(conn)

        assignments = generate_assignments(
            candidate_sets
        )
       
        save_assignments(
            conn,
            assignments,
        )

    finally:

        conn.close()


if __name__ == "__main__":
    main()