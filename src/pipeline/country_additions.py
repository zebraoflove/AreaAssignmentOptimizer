"""
Добавление вручную определённых государств и территорий
в обработанный набор стран.
"""

from src.config.countries import MANUAL_COUNTRIES


def apply_manual_country_additions(rows):
    """
    Добавляет ручные государства и территории,
    отсутствующие в countries_raw.

    Существующие записи не изменяются.
    """

    existing_names = {
        row["name"].strip()
        for row in rows
    }

    result = list(rows)

    for name, data in MANUAL_COUNTRIES.items():
        name = name.strip()

        if name in existing_names:
            continue

        result.append(
            {
                "name": name,
                "iso_alpha2": data.get("iso_alpha2"),
                "iso_alpha3": data.get("iso_alpha3"),
                "continent": data.get("continent"),
                "area_km2": data["area_km2"],
            }
        )

    return result