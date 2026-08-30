"""
Запуск эксперимента на актуальном наборе данных.

Перед запуском алгоритма полностью пересобирает:
- countries_raw;
- subjects_raw;
- countries_final;
- candidate_sets.

После этого запускает выбранный алгоритм,
оценивает назначения и сохраняет Excel-отчёт.
"""

from pathlib import Path

from src.common.database import connect

from src.importers.countries import (
    import_countries,
)

from src.importers.subjects import (
    prepare_subjects,
)

from src.importers.import_adjustments import (
    import_adjustments,
)

from src.algorithms import greedy as algorithm

from src.analysis.evaluate_assignments import (
    evaluate_assignments,
)

from src.experiments.export_excel import (
    export_excel,
)


EXPORTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "exports"
    / "experiments"
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

        print(
            f"{index}. {section}"
        )

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
        "Unique subjects",
        statistics["unique_subjects"],
    )

    print_key_value(
        "Unique countries",
        statistics["unique_countries"],
    )

    print_key_value(
        "Total absolute error",
        f"{statistics['total_absolute_error']:.1f} км²",
    )

    print_key_value(
        "Average absolute error",
        f"{statistics['average_absolute_error']:.1f} км²",
    )

    print_key_value(
        "Median absolute error",
        f"{statistics['median_absolute_error']:.1f} км²",
    )

    print_key_value(
        "Maximum absolute error",
        f"{statistics['maximum_absolute_error']:.1f} км²",
    )

    print_key_value(
        "Average relative error",
        f"{statistics['average_relative_error']:.2f}%",
    )

    print_key_value(
        "Median relative error",
        f"{statistics['median_relative_error']:.2f}%",
    )

    print_key_value(
        "Maximum relative error",
        f"{statistics['maximum_relative_error']:.2f}%",
    )

    print_key_value(
        "Constraint violations",
        statistics["constraint_violations"],
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
        "Absolute error",
        f"{statistics['best_match']['absolute_error']:.1f} км²",
    )

    print_key_value(
        "Relative error",
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
        "Absolute error",
        f"{statistics['worst_match']['absolute_error']:.1f} км²",
    )

    print_key_value(
        "Relative error",
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


def rebuild_pipeline():
    """
    Полностью пересобирает данные перед экспериментом.

    Порядок:
    1. countries_raw;
    2. subjects_raw;
    3. countries_final;
    4. candidate_sets.
    """

    conn = connect()

    try:

        import_countries(
            conn,
        )

        conn.commit()

    finally:

        conn.close()

    conn = connect()

    try:

        prepare_subjects(
            conn,
        )

        conn.commit()

    finally:

        conn.close()

    import_adjustments()


def main():

    # --------------------------------------------------
    # 1. Полностью пересобираем pipeline.
    # --------------------------------------------------

    rebuild_pipeline()

    # --------------------------------------------------
    # 2. Запускаем алгоритм на актуальных candidate_sets.
    # --------------------------------------------------

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

        # --------------------------------------------------
        # 3. Сохраняем Excel-отчёт.
        # --------------------------------------------------

        experiment_dir = (
            EXPORTS_DIR
            / "greedy_original_constraint"
        )

        experiment_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            experiment_dir
            / "report.xlsx"
        )

        export_excel(
            conn,
            configuration,
            statistics,
            output_path,
        )

        # --------------------------------------------------
        # 4. Печатаем отчёт.
        # --------------------------------------------------

        print_report(
            configuration,
            statistics,
        )

    finally:

        conn.close()


if __name__ == "__main__":
    main()