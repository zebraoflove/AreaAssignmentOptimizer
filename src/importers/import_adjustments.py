"""
Формирование countries_final из countries_raw
с применением территориальных корректировок.
"""

from src.common.database import connect
from src.algorithms.generate_candidate_sets import rebuild_candidate_sets
from src.importers.manual_country_additions import (
    apply_manual_country_additions,
)
from database.territory_adjustments import (
    ADJUSTMENTS as TERRITORY_ADJUSTMENTS,
    AGGREGATE_COUNTRIES,
)
from data.source.countries.country_metadata import COUNTRY_METADATA


COUNTRY_NAME_RENAMES = {
    "Palestinian Territory Occupied": "Palestine",
    "South Georgia": "South Georgia and the South Sandwich Islands",
}


EXCLUDED_COUNTRIES_FINAL = {
    "Antarctica",
}


def read_countries_raw(conn):
    """Читает исходные записи из countries_raw."""

    rows = conn.execute("""
        SELECT
            name,
            iso_alpha2,
            iso_alpha3,
            continent,
            area_km2
        FROM countries_raw
    """).fetchall()

    return [
        {
            "name": row["name"],
            "iso_alpha2": row["iso_alpha2"],
            "iso_alpha3": row["iso_alpha3"],
            "continent": row["continent"],
            "area_km2": row["area_km2"],
        }
        for row in rows
    ]


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


def get_metadata(name):
    """Возвращает status и notes из ручных метаданных."""

    metadata = COUNTRY_METADATA.get(name)

    if metadata is None:
        return "independent", None

    return (
        metadata.get("status", "independent"),
        metadata.get("notes"),
    )


def ensure_aggregate_country(countries, name):
    """Создаёт промежуточную запись агрегированного суверена."""

    if name in countries:
        return

    countries[name] = {
        "name": name,
        "iso_alpha2": "",
        "iso_alpha3": "",
        "continent": "",
        "area_km2": 0,
    }


def merge_continents(countries, source_name, target_name):
    """
    Добавляет уникальные континенты source_name к target_name.

    Континенты хранятся в виде строки:
        "Americas"
        "Americas; Oceania"
        "Americas; Europe; Oceania"

    "Polar" используется как специальная географическая
    категория территории, но не добавляется к континентам
    агрегированного государства.

    Дубликаты не добавляются.
    """

    source_continent = (
        countries[source_name].get("continent") or ""
    )

    target_continent = (
        countries[target_name].get("continent") or ""
    )

    continents = []

    for value in (
        target_continent,
        source_continent,
    ):
        for continent in value.split(";"):

            continent = continent.strip()

            if (
                continent
                and continent != "Polar"
                and continent not in continents
            ):
                continents.append(continent)

    countries[target_name]["continent"] = "; ".join(
        continents
    )


def apply_territory_adjustments(rows):
    """
    Применяет территориальные корректировки к списку стран.

    Правила:

    1. area_km2 указана явно:
       - используется указанное значение;
       - territory может отсутствовать в countries_raw.

    2. area_km2 == None:
       - territory обязана существовать в countries_raw;
       - площадь берётся из записи territory.

    3. Положительная площадь:
       - subtract_from получает вычитание;
       - add_to получает прибавление.

    4. Отрицательная площадь:
       - означает обратное направление той же операции;
       - subtract_from получает прибавление;
       - add_to получает вычитание.

    5. Если territory отсутствует в countries_raw, но площадь
       указана явно, корректировка всё равно выполняется.
       Это используется, например, для Крыма, Севастополя,
       ДНР, ЛНР, Запорожской и Херсонской областей, когда
       эти территории не представлены отдельными странами
       в countries_raw.

    6. Если subtract_from == territory и territory существует,
       положительная корректировка полностью передаёт площадь
       территории add_to, поэтому площадь territory становится 0.

    7. Площадь 0 допустима на промежуточном этапе.

    8. Для агрегированных государств после всех корректировок
       формируется уникальный список континентов их территорий.
    """

    # --------------------------------------------------------
    # Сохраняем исходные континенты.
    # --------------------------------------------------------

    source_continents = {
        row["name"]: row.get("continent")
        for row in rows
    }

    # --------------------------------------------------------
    # Копируем страны в рабочую структуру.
    # --------------------------------------------------------

    countries = {
        row["name"]: {
            **row,
            "area_km2": float(row["area_km2"]),
        }
        for row in rows
    }

    # --------------------------------------------------------
    # Применяем корректировки.
    # --------------------------------------------------------

    for adjustment in TERRITORY_ADJUSTMENTS:

        territory = adjustment["territory"]
        area = adjustment.get("area_km2")
        subtract_from = adjustment["subtract_from"]
        add_to = adjustment["add_to"]

        # ----------------------------------------------------
        # Определяем площадь корректировки.
        #
        # Если площадь задана явно, territory может отсутствовать.
        #
        # Если площадь не задана, territory обязан существовать,
        # поскольку иначе невозможно определить его площадь.
        # ----------------------------------------------------

        if area is None:

            if territory not in countries:
                raise ValueError(
                    f"Territory not found in countries_raw and "
                    f"area_km2 is None: {territory}"
                )

            area = float(
                countries[territory]["area_km2"]
            )

        else:
            area = float(area)

        # Нулевая корректировка не имеет смысла.
        if area == 0:
            raise ValueError(
                f"Invalid adjustment area for {territory}: {area}"
            )

        # ----------------------------------------------------
        # Источник вычитания обязан существовать.
        #
        # Например:
        #
        # subtract_from = "Ukraine"
        # add_to        = "Russia"
        #
        # Для Крыма territory может отсутствовать,
        # но Ukraine и Russia существуют.
        # ----------------------------------------------------

        if subtract_from not in countries:
            raise ValueError(
                f"subtract_from not found in countries_raw: "
                f"{subtract_from}"
            )

        # ----------------------------------------------------
        # add_to может быть агрегированным государством,
        # которого изначально нет в countries_raw.
        # ----------------------------------------------------

        ensure_aggregate_country(
            countries,
            add_to,
        )

        if add_to not in countries:
            raise ValueError(
                f"add_to not found in countries_raw or aggregate countries: "
                f"{add_to}"
            )

        # ----------------------------------------------------
        # Континенты.
        #
        # Выполняем только если territory реально существует
        # как отдельная запись.
        # ----------------------------------------------------

        if (
            territory != add_to
            and territory in countries
        ):
            merge_continents(
                countries,
                territory,
                add_to,
            )

        # ----------------------------------------------------
        # Применяем математическую операцию.
        #
        # area > 0:
        #
        #     subtract_from -= area
        #     add_to       += area
        #
        # area < 0:
        #
        #     subtract_from -= (-area)
        #     add_to       += (-area)
        #
        # То есть отрицательная площадь автоматически
        # инвертирует направление переноса:
        #
        #     subtract_from += abs(area)
        #     add_to       -= abs(area)
        # ----------------------------------------------------

        if area > 0:
            countries[subtract_from]["area_km2"] -= area
            countries[add_to]["area_km2"] += area
        else:
            countries[subtract_from]["area_km2"] -= abs(area)

        # ----------------------------------------------------
        # Если territory существует отдельно и является
        # источником операции, контролируем её площадь.
        # ----------------------------------------------------

        if territory in countries:

            if countries[territory]["area_km2"] < -1e-9:
                raise ValueError(
                    f"Negative area for {territory}: "
                    f"{countries[territory]['area_km2']}"
                )

            # Полное поглощение.
            if (
                subtract_from == territory
                and area > 0
                and abs(countries[territory]["area_km2"]) < 1e-9
            ):
                countries[territory]["area_km2"] = 0.0

        # ----------------------------------------------------
        # Контроль источника и получателя.
        # ----------------------------------------------------

        if countries[subtract_from]["area_km2"] < -1e-9:
            raise ValueError(
                f"Negative area for {subtract_from}: "
                f"{countries[subtract_from]['area_km2']}"
            )

        if countries[add_to]["area_km2"] < -1e-9:
            raise ValueError(
                f"Negative area for {add_to}: "
                f"{countries[add_to]['area_km2']}"
            )

        # Убираем возможный микроскопический отрицательный
        # остаток из-за операций с float.
        if abs(countries[subtract_from]["area_km2"]) < 1e-9:
            countries[subtract_from]["area_km2"] = 0.0

        if abs(countries[add_to]["area_km2"]) < 1e-9:
            countries[add_to]["area_km2"] = 0.0

    # --------------------------------------------------------
    # Континенты агрегированных государств.
    # --------------------------------------------------------

    for aggregate_name, territories in AGGREGATE_COUNTRIES.items():

        if aggregate_name not in countries:
            continue

        continents = sorted(
            {
                source_continents[name]
                for name in territories
                if source_continents.get(name)
            }
        )

        countries[aggregate_name]["continent"] = "; ".join(
            continents
        )

    # --------------------------------------------------------
    # Финальный результат.
    # --------------------------------------------------------

    return list(countries.values())


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
            # Важно:
            # территория могла быть переименована до применения
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


def import_adjustments():
    """Полный процесс применения территориальных корректировок."""

    conn = connect()

    try:
        rows = read_countries_raw(conn)

        rows = normalize_country_names(rows)

        rows = apply_manual_country_additions(rows)
        
        rows = apply_territory_adjustments(rows)

        upsert_countries_final(
            conn,
            rows,
        )

        rebuild_candidate_sets(conn)

        conn.commit()

    finally:
        conn.close()

    print("Territory adjustments applied.")


def main():
    import_adjustments()


if __name__ == "__main__":
    main()