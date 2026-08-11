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

    subjects = set()

    countries = set()

    constraint_violations = 0

    for row in rows:

        subjects.add(
            row["subject_name"]
        )

        countries.add(
            row["country_name"]
        )

        absolute_error = abs(
            row["subject_area"]
            -
            row["country_area"]
        )

        relative_error = (
            absolute_error
            /
            row["subject_area"]
        ) * 100

        absolute_errors.append(
            absolute_error
        )

        relative_errors.append(
            relative_error
        )

        if (
            row["country_area"]
            >
            row["subject_area"]
        ):
            constraint_violations += 1

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

    sorted_absolute_errors = sorted(
        absolute_errors
    )

    sorted_relative_errors = sorted(
        relative_errors
    )

    count = len(rows)

    middle = count // 2

    if count % 2 == 0:

        median_absolute_error = (
            sorted_absolute_errors[middle - 1]
            +
            sorted_absolute_errors[middle]
        ) / 2

        median_relative_error = (
            sorted_relative_errors[middle - 1]
            +
            sorted_relative_errors[middle]
        ) / 2

    else:

        median_absolute_error = (
            sorted_absolute_errors[middle]
        )

        median_relative_error = (
            sorted_relative_errors[middle]
        )

    return {

        "count":
            count,

        "unique_subjects":
            len(subjects),

        "unique_countries":
            len(countries),

        "total_absolute_error":
            sum(absolute_errors),

        "average_absolute_error":
            sum(absolute_errors)
            /
            count,

        "median_absolute_error":
            median_absolute_error,

        "maximum_absolute_error":
            max(absolute_errors),

        "average_relative_error":
            sum(relative_errors)
            /
            count,

        "median_relative_error":
            median_relative_error,

        "maximum_relative_error":
            max(relative_errors),

        "constraint_violations":
            constraint_violations,

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


def evaluate_assignments(conn):
    """Вычисляет статистику распределения."""

    rows = read_assignments(conn)

    return calculate_statistics(rows)


def main():

    conn = connect()

    try:

        stats = evaluate_assignments(conn)

        print_statistics(stats)

    finally:

        conn.close()


if __name__ == "__main__":
    main()