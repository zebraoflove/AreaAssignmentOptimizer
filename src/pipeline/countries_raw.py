"""
Чтение исходного набора стран из countries_raw.
"""


def read_countries_raw(conn):
    """Читает исходные записи из countries_raw."""

    rows = conn.execute(
        """
        SELECT
            name,
            iso_alpha2,
            iso_alpha3,
            continent,
            area_km2
        FROM countries_raw
        """
    ).fetchall()

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