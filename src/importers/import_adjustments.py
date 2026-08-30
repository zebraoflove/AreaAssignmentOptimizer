"""
Формирование countries_final из countries_raw
с применением территориальных корректировок.
"""

from src.common.database import connect
from src.algorithms.generate_candidate_sets import rebuild_candidate_sets
from src.pipeline.territory_adjustments import (
    apply_territory_adjustments,
)
from src.pipeline.countries_final import (
    normalize_country_names,
    upsert_countries_final,
)
from src.pipeline.country_additions import (
    apply_manual_country_additions,
)
from src.pipeline.countries_raw import read_countries_raw


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