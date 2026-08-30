"""
Формирование и обновление countries_final.

Содержит:
- миграцию ссылок при переименовании стран;
- миграцию ссылок при полном поглощении территорий;
- пересборку countries_final из обработанного набора.
"""

from data.source.countries.country_metadata import COUNTRY_METADATA
from database.territory_adjustments import (
    ADJUSTMENTS as TERRITORY_ADJUSTMENTS,
)
from src.config.countries import (
    COUNTRY_NAME_RENAMES,
    EXCLUDED_COUNTRIES_FINAL,
)


def get_metadata(name):
    """Возвращает status и notes для страны."""
    metadata = COUNTRY_METADATA.get(name, {})

    return (
        metadata.get("status"),
        metadata.get("notes"),
    )


def migrate_absorbed_territory_references(
    conn,
    territory_name,
    sovereign_name,
):
    """
    Переносит ссылки с поглощённой территории на суверена.

    Если такая ссылка на суверена уже существует в той же
    candidate_set или assignment, дублирующая ссылка удаляется.
    """

    territory_row = conn.execute(
        """
        SELECT id
        FROM countries_final
        WHERE name = ?
        """,
        (territory_name,),
    ).fetchone()

    sovereign_row = conn.execute(
        """
        SELECT id
        FROM countries_final
        WHERE name = ?
        """,
        (sovereign_name,),
    ).fetchone()

    if territory_row is None:
        return

    if sovereign_row is None:
        raise ValueError(
            f"Sovereign not found in countries_final: "
            f"{sovereign_name}"
        )

    territory_id = territory_row["id"]
    sovereign_id = sovereign_row["id"]

    # ---------------------------------------------------------
    # candidate_set_items
    # ---------------------------------------------------------

    candidate_refs = conn.execute(
        """
        SELECT id, candidate_set_id
        FROM candidate_set_items
        WHERE country_id = ?
        """,
        (territory_id,),
    ).fetchall()

    for ref in candidate_refs:
        duplicate = conn.execute(
            """
            SELECT id
            FROM candidate_set_items
            WHERE candidate_set_id = ?
              AND country_id = ?
            """,
            (
                ref["candidate_set_id"],
                sovereign_id,
            ),
        ).fetchone()

        if duplicate is not None:
            conn.execute(
                """
                DELETE FROM candidate_set_items
                WHERE id = ?
                """,
                (ref["id"],),
            )
        else:
            conn.execute(
                """
                UPDATE candidate_set_items
                SET country_id = ?
                WHERE id = ?
                """,
                (
                    sovereign_id,
                    ref["id"],
                ),
            )

    # ---------------------------------------------------------
    # assignment_items
    # ---------------------------------------------------------

    assignment_refs = conn.execute(
        """
        SELECT id, assignment_id
        FROM assignment_items
        WHERE country_id = ?
        """,
        (territory_id,),
    ).fetchall()

    for ref in assignment_refs:
        duplicate = conn.execute(
            """
            SELECT id
            FROM assignment_items
            WHERE assignment_id = ?
              AND country_id = ?
            """,
            (
                ref["assignment_id"],
                sovereign_id,
            ),
        ).fetchone()

        if duplicate is not None:
            conn.execute(
                """
                DELETE FROM assignment_items
                WHERE id = ?
                """,
                (ref["id"],),
            )
        else:
            conn.execute(
                """
                UPDATE assignment_items
                SET country_id = ?
                WHERE id = ?
                """,
                (
                    sovereign_id,
                    ref["id"],
                ),
            )


def migrate_country_references(
    conn,
    old_name,
    new_name,
):
    """
    Переносит ссылки с переименованной страны
    на новую запись страны.

    Если ссылка на новое имя уже существует
    в том же candidate_set или assignment,
    старая ссылка удаляется.
    """

    old_row = conn.execute(
        """
        SELECT id
        FROM countries_final
        WHERE name = ?
        """,
        (old_name,),
    ).fetchone()

    new_row = conn.execute(
        """
        SELECT id
        FROM countries_final
        WHERE name = ?
        """,
        (new_name,),
    ).fetchone()

    if old_row is None:
        return

    if new_row is None:
        raise ValueError(
            f"Renamed country not found in countries_final: "
            f"{new_name}"
        )

    old_id = old_row["id"]
    new_id = new_row["id"]

    # ---------------------------------------------------------
    # candidate_set_items
    # ---------------------------------------------------------

    candidate_refs = conn.execute(
        """
        SELECT id, candidate_set_id
        FROM candidate_set_items
        WHERE country_id = ?
        """,
        (old_id,),
    ).fetchall()

    for ref in candidate_refs:
        duplicate = conn.execute(
            """
            SELECT id
            FROM candidate_set_items
            WHERE candidate_set_id = ?
              AND country_id = ?
            """,
            (
                ref["candidate_set_id"],
                new_id,
            ),
        ).fetchone()

        if duplicate is not None:
            conn.execute(
                """
                DELETE FROM candidate_set_items
                WHERE id = ?
                """,
                (ref["id"],),
            )
        else:
            conn.execute(
                """
                UPDATE candidate_set_items
                SET country_id = ?
                WHERE id = ?
                """,
                (
                    new_id,
                    ref["id"],
                ),
            )

    # ---------------------------------------------------------
    # assignment_items
    # ---------------------------------------------------------

    assignment_refs = conn.execute(
        """
        SELECT id, assignment_id
        FROM assignment_items
        WHERE country_id = ?
        """,
        (old_id,),
    ).fetchall()

    for ref in assignment_refs:
        duplicate = conn.execute(
            """
            SELECT id
            FROM assignment_items
            WHERE assignment_id = ?
              AND country_id = ?
            """,
            (
                ref["assignment_id"],
                new_id,
            ),
        ).fetchone()

        if duplicate is not None:
            conn.execute(
                """
                DELETE FROM assignment_items
                WHERE id = ?
                """,
                (ref["id"],),
            )
        else:
            conn.execute(
                """
                UPDATE assignment_items
                SET country_id = ?
                WHERE id = ?
                """,
                (
                    new_id,
                    ref["id"],
                ),
            )


def normalize_country_names(rows):
    """Нормализует названия стран перед дальнейшей обработкой."""

    return [
        {
            **row,
            "name": COUNTRY_NAME_RENAMES.get(
                row["name"].strip(),
                row["name"].strip(),
            ),
        }
        for row in rows
    ]


def upsert_countries_final(conn, rows):
    """
    Пересобирает countries_final из обработанного набора.

    Правила:

    - записи с area_km2 == 0 не попадают в countries_final;
    - status и notes берутся из COUNTRY_METADATA;
    - отсутствующие записи добавляются;
    - существующие записи обновляются;
    - перед удалением поглощённых территорий их ссылки
      мигрируются на итогового суверена;
    - итоговый суверен сначала добавляется/обновляется,
      поэтому миграция ссылок не нарушает внешние ключи;
    - записи, которых больше нет в итоговом наборе,
      удаляются из countries_final.
    """

    valid_rows = [
        row
        for row in rows
        if (
            float(row["area_km2"]) > 0
            and row["name"].strip()
            not in EXCLUDED_COUNTRIES_FINAL
        )
    ]

    final_names = {
        row["name"].strip()
        for row in valid_rows
    }

    # --------------------------------------------------------
    # 1. Добавляем / обновляем все итоговые записи.
    # --------------------------------------------------------

    for row in valid_rows:
        name = row["name"].strip()

        status, notes = get_metadata(name)

        conn.execute(
            """
            INSERT INTO countries_final (
                name,
                iso_alpha2,
                iso_alpha3,
                continent,
                area_km2,
                status,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                iso_alpha2 = excluded.iso_alpha2,
                iso_alpha3 = excluded.iso_alpha3,
                continent = excluded.continent,
                area_km2 = excluded.area_km2,
                status = excluded.status,
                notes = excluded.notes
            """,
            (
                name,
                row.get("iso_alpha2") or None,
                row.get("iso_alpha3") or None,
                row.get("continent") or None,
                int(row["area_km2"]),
                status,
                notes,
            ),
        )

    # --------------------------------------------------------
    # 2. Удаляем записи, которых больше нет в итоговом наборе.
    # --------------------------------------------------------

    existing_rows = conn.execute(
        "SELECT name FROM countries_final"
    ).fetchall()

    for row in existing_rows:
        name = row["name"]

        if name in final_names:
            continue

        # ----------------------------------------------------
        # Сначала проверяем полное поглощение.
        #
        # Территория могла быть переименована до применения
        # TERRITORY_ADJUSTMENTS, поэтому adjustment["territory"]
        # может содержать уже новое имя.
        # ----------------------------------------------------

        renamed_to = COUNTRY_NAME_RENAMES.get(name)
        absorbed_adjustment = None

        if renamed_to is not None:
            absorbed_adjustment = next(
                (
                    item
                    for item in TERRITORY_ADJUSTMENTS
                    if item["territory"] == renamed_to
                    and item["subtract_from"] == renamed_to
                    and item["add_to"] != renamed_to
                ),
                None,
            )

        # ----------------------------------------------------
        # Если переименованная территория полностью поглощена,
        # ссылки сразу мигрируются на итогового суверена.
        # ----------------------------------------------------

        if absorbed_adjustment is not None:
            migrate_country_references(
                conn,
                name,
                absorbed_adjustment["add_to"],
            )

        else:
            # ------------------------------------------------
            # Обычное переименование.
            # ------------------------------------------------

            if renamed_to is not None:
                migrate_country_references(
                    conn,
                    name,
                    renamed_to,
                )

            else:
                # --------------------------------------------
                # Обычное полное поглощение без переименования.
                # --------------------------------------------

                adjustment = next(
                    (
                        item
                        for item in TERRITORY_ADJUSTMENTS
                        if item["territory"] == name
                        and item["subtract_from"] == name
                        and item["add_to"] != name
                    ),
                    None,
                )

                if adjustment is not None:
                    migrate_absorbed_territory_references(
                        conn,
                        name,
                        adjustment["add_to"],
                    )

        conn.execute(
            "DELETE FROM countries_final WHERE name = ?",
            (name,),
        )