from src.common.database import connect

from src.algorithms import greedy as algorithm

from src.analysis.evaluate_assignments import (
    evaluate_assignments,
)


def print_header():
    """Выводит заголовок отчёта."""

    print()

    print("=" * 60)

    print("AREA ASSIGNMENT OPTIMIZER")

    print("Experiment Report")

    print("=" * 60)

    print()


def print_contents():
    """Выводит оглавление отчёта."""

    sections = [
        "Algorithm configuration",
        "Assignment statistics",
    ]

    print("Contents")

    print("--------")

    print()

    for index, section in enumerate(
        sections,
        start=1,
    ):

        print(f"{index}. {section}")

    print()


def print_key_value(
    key,
    value,
):
    """Выводит пару «ключ–значение»."""

    print(
        f"{key + ':':25}"
        f"{value}"
    )


def print_algorithm_configuration(
    configuration,
):
    """Выводит настройки алгоритма."""

    print("-" * 60)

    print()

    print("## Algorithm configuration")

    print()

    for key, value in configuration.items():

        print_key_value(
            key,
            value,
        )

    print()


def print_assignment_statistics(
    statistics,
):
    """Выводит статистику распределения."""

    print("-" * 60)

    print()

    print("## Assignment statistics")

    print()

    print_key_value(
        "Assignments",
        statistics["count"],
    )

    print_key_value(
        "Average absolute error",
        f"{statistics['average_absolute_error']:.1f} km²",
    )

    print_key_value(
        "Average relative error",
        f"{statistics['average_relative_error']:.2f}%",
    )

    print()

    print("Best match")

    print("----------")

    print()

    print_key_value(
        "Subject",
        statistics["best_match"]["subject_name"],
    )

    print_key_value(
        "Country",
        statistics["best_match"]["country_name"],
    )

    print_key_value(
        "Error",
        f"{statistics['best_match']['relative_error']:.2f}%",
    )

    print()

    print("Worst match")

    print("-----------")

    print()

    print_key_value(
        "Subject",
        statistics["worst_match"]["subject_name"],
    )

    print_key_value(
        "Country",
        statistics["worst_match"]["country_name"],
    )

    print_key_value(
        "Error",
        f"{statistics['worst_match']['relative_error']:.2f}%",
    )

    print()


def print_report(
    configuration,
    statistics,
):
    """Выводит полный отчёт."""

    print_header()

    print_contents()

    print_algorithm_configuration(
        configuration,
    )

    print_assignment_statistics(
        statistics,
    )

def main():

    conn = connect()

    try:

        configuration = (
            algorithm.get_configuration()
        )

        candidate_sets = (
            algorithm.read_candidate_sets(
                conn,
            )
        )

        assignments = (
            algorithm.generate_assignments(
                candidate_sets,
            )
        )

        algorithm.save_assignments(
            conn,
            assignments,
        )

        statistics = (
            evaluate_assignments(
                conn,
            )
        )

        print_report(
            configuration,
            statistics,
        )

    finally:

        conn.close()

if __name__ == "__main__":
    main()