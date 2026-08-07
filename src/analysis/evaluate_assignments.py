from src.common.database import connect

DEBUG = True


def read_assignments(conn):
    """Читает назначения вместе с площадями."""

    rows = conn.execute(
        """
        SELECT

            s.name AS subject_name,
            s.area_km2 AS subject_area,

            c.name AS country_name,
            c.area_km2 AS country_area

        FROM assignments a

        JOIN assignment_items ai
            ON ai.assignment_id = a.id

        JOIN subjects_final s
            ON s.id = a.subject_id

        JOIN countries_final c
            ON c.id = ai.country_id

        ORDER BY
            s.name
        """
    ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def calculate_statistics(rows):
    """Вычисляет статистику качества распределения."""

    absolute_errors = []

    relative_errors = []

    best_match = None

    worst_match = None

    for row in rows:

        absolute_error = abs(
            row["subject_area"] -
            row["country_area"]
        )

        relative_error = (
            absolute_error /
            row["subject_area"]
        ) * 100

        absolute_errors.append(
            absolute_error
        )

        relative_errors.append(
            relative_error
        )

        result = {
            **row,
            "absolute_error": absolute_error,
            "relative_error": relative_error,
        }

        if (
            best_match is None
            or
            result["relative_error"]
            <
            best_match["relative_error"]
        ):
            best_match = result

        if (
            worst_match is None
            or
            result["relative_error"]
            >
            worst_match["relative_error"]
        ):
            worst_match = result

    return {

        "count": len(rows),

        "average_absolute_error":
            sum(absolute_errors)
            /
            len(absolute_errors),

        "average_relative_error":
            sum(relative_errors)
            /
            len(relative_errors),

        "best_match":
            best_match,

        "worst_match":
            worst_match,

    }


def print_statistics(stats):
    """Выводит результаты анализа."""

    print()

    print("Assignment statistics")

    print("---------------------")

    print(
        f"Assignments: "
        f"{stats['count']}"
    )

    print(
        f"Average absolute error: "
        f"{stats['average_absolute_error']:.1f} km²"
    )

    print(
        f"Average relative error: "
        f"{stats['average_relative_error']:.2f}%"
    )

    print()

    print("Best match")

    print(
        f"{stats['best_match']['subject_name']}"
    )

    print(
        f"→ {stats['best_match']['country_name']}"
    )

    print(
        f"{stats['best_match']['relative_error']:.2f}%"
    )

    print()

    print("Worst match")

    print(
        f"{stats['worst_match']['subject_name']}"
    )

    print(
        f"→ {stats['worst_match']['country_name']}"
    )

    print(
        f"{stats['worst_match']['relative_error']:.2f}%"
    )


def main():

    conn = connect()

    try:

        rows = read_assignments(conn)

        stats = calculate_statistics(rows)

        print_statistics(stats)

    finally:

        conn.close()


if __name__ == "__main__":
    main()