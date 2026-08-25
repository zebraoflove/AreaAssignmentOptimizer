from typing import List, Dict


NEW_SUBJECTS = [
    {
        "name": "Донецкая Народная Республика",
        "type": "республика",
        "federal_district": "Управляется напрямую",
        "area_km2": 26520.0,
    },
    {
        "name": "Луганская Народная Республика",
        "type": "республика",
        "federal_district": "Управляется напрямую",
        "area_km2": 26680.0,
    },
    {
        "name": "Запорожская область",
        "type": "область",
        "federal_district": "Управляется напрямую",
        "area_km2": 27180.0,
    },
    {
        "name": "Херсонская область",
        "type": "область",
        "federal_district": "Управляется напрямую",
        "area_km2": 28460.0,
    },
]


def read_new_subjects() -> List[Dict]:
    """Возвращает данные новых субъектов РФ."""
    return NEW_SUBJECTS.copy()