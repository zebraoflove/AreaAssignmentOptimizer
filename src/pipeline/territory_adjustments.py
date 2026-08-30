"""
Применение территориальных корректировок
к рабочему набору стран.
"""

from database.territory_adjustments import (
    ADJUSTMENTS as TERRITORY_ADJUSTMENTS,
    AGGREGATE_COUNTRIES,
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