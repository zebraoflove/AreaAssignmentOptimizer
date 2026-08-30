"""
Интеграционный тест полного текущего конвейера.
"""

import shutil
import sqlite3
from pathlib import Path

from src.common.config import DATABASE_PATH
from src.common.database import connect
from src.importers.countries import import_countries
from src.importers.subjects import prepare_subjects
from src.importers.import_adjustments import import_adjustments


def test_full_pipeline():
    """
    Прогоняет весь текущий конвейер целиком.

    Проверяет:
    - импорт стран в countries_raw;
    - подготовку субъектов в subjects_raw;
    - применение территориальных корректировок;
    - формирование countries_final;
    - формирование candidate_sets;
    - ссылочную целостность;
    - отсутствие отрицательных и нулевых площадей;
    - отсутствие дубликатов.

    Рабочая база перед тестом сохраняется и после теста
    восстанавливается.
    """

    database_path = Path(DATABASE_PATH)
    backup_path = database_path.with_suffix(".test_backup.db")

    shutil.copy2(
        database_path,
        backup_path,
    )

    try:
        # --------------------------------------------------
        # 1. Страны
        # --------------------------------------------------

        conn = connect()

        try:
            country_count = import_countries(conn)

            conn.commit()

            assert country_count == 248

            countries_raw_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM countries_raw
                """
            ).fetchone()[0]

            assert countries_raw_count == country_count

        finally:
            conn.close()

        # --------------------------------------------------
        # 2. Субъекты
        # --------------------------------------------------

        conn = connect()

        try:
            subject_count = prepare_subjects(conn)

            conn.commit()

            assert subject_count > 0

            subjects_raw_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM subjects_raw
                """
            ).fetchone()[0]

            assert subjects_raw_count == subject_count

        finally:
            conn.close()

        # --------------------------------------------------
        # 3. Территориальные корректировки
        # --------------------------------------------------

        import_adjustments()

        # --------------------------------------------------
        # 4. Проверяем итоговую базу
        # --------------------------------------------------

        conn = connect()

        try:
            # ----------------------------------------------
            # countries_final существует и не пустая
            # ----------------------------------------------

            countries_final_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM countries_final
                """
            ).fetchone()[0]

            assert countries_final_count > 0

            # ----------------------------------------------
            # countries_final не содержит нулевые площади
            # ----------------------------------------------

            invalid_countries = conn.execute(
                """
                SELECT name, area_km2
                FROM countries_final
                WHERE area_km2 <= 0
                """
            ).fetchall()

            assert not invalid_countries

            # ----------------------------------------------
            # Нет дубликатов стран
            # ----------------------------------------------

            duplicate_countries = conn.execute(
                """
                SELECT name, COUNT(*) AS count
                FROM countries_final
                GROUP BY name
                HAVING COUNT(*) > 1
                """
            ).fetchall()

            assert not duplicate_countries

            # ----------------------------------------------
            # subjects_raw не пустая
            # ----------------------------------------------

            subjects_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM subjects_raw
                """
            ).fetchone()[0]

            assert subjects_count == subject_count

            # ----------------------------------------------
            # Нет отрицательных площадей субъектов
            # ----------------------------------------------

            invalid_subjects = conn.execute(
                """
                SELECT name, area_km2
                FROM subjects_raw
                WHERE area_km2 <= 0
                """
            ).fetchall()

            assert not invalid_subjects

            # ----------------------------------------------
            # candidate_sets не пустые
            # ----------------------------------------------

            candidate_sets_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM candidate_sets
                """
            ).fetchone()[0]

            assert candidate_sets_count > 0

            # ----------------------------------------------
            # candidate_set_items не пустые
            # ----------------------------------------------

            candidate_items_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM candidate_set_items
                """
            ).fetchone()[0]

            assert candidate_items_count > 0

            # ----------------------------------------------
            # Все candidate_set_items ссылаются
            # на существующие candidate_sets
            # ----------------------------------------------

            invalid_candidate_sets = conn.execute(
                """
                SELECT csi.id
                FROM candidate_set_items csi
                LEFT JOIN candidate_sets cs
                    ON cs.id = csi.candidate_set_id
                WHERE cs.id IS NULL
                """
            ).fetchall()

            assert not invalid_candidate_sets

            # ----------------------------------------------
            # Все candidate_set_items ссылаются
            # на существующие countries_final
            # ----------------------------------------------

            invalid_candidate_countries = conn.execute(
                """
                SELECT csi.id
                FROM candidate_set_items csi
                LEFT JOIN countries_final c
                    ON c.id = csi.country_id
                WHERE c.id IS NULL
                """
            ).fetchall()

            assert not invalid_candidate_countries

            # ----------------------------------------------
            # Нет дубликатов стран внутри candidate_set
            # ----------------------------------------------

            duplicate_candidate_items = conn.execute(
                """
                SELECT
                    candidate_set_id,
                    country_id,
                    COUNT(*) AS count
                FROM candidate_set_items
                GROUP BY
                    candidate_set_id,
                    country_id
                HAVING COUNT(*) > 1
                """
            ).fetchall()

            assert not duplicate_candidate_items

            # ----------------------------------------------
            # Все страны из candidate_set_items существуют
            # и имеют положительную площадь
            # ----------------------------------------------

            invalid_candidate_area = conn.execute(
                """
                SELECT csi.id
                FROM candidate_set_items csi
                JOIN countries_final c
                    ON c.id = csi.country_id
                WHERE c.area_km2 <= 0
                """
            ).fetchall()

            assert not invalid_candidate_area

        finally:
            conn.close()

    finally:
        # --------------------------------------------------
        # Восстанавливаем исходную БД
        # --------------------------------------------------

        shutil.copy2(
            backup_path,
            database_path,
        )

        backup_path.unlink()