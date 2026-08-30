"""
Настройки обработки стран.
"""


# ---------------------------------------------------------
# Ручные государства и территории
# ---------------------------------------------------------

MANUAL_COUNTRIES = {
    "Abkhazia": {
        "iso_alpha2": None,
        "iso_alpha3": "XAB",
        "continent": "Asia",
        "area_km2": 8660,
    },
    "Ambazonia": {
        "iso_alpha2": None,
        "iso_alpha3": "XAM",
        "continent": "Africa",
        "area_km2": 42710,
    },
    "Azad Kashmir": {
        "iso_alpha2": None,
        "iso_alpha3": "XAK",
        "continent": "Asia",
        "area_km2": 13297,
    },
    "Northern Cyprus": {
        "iso_alpha2": None,
        "iso_alpha3": "XNC",
        "continent": "Asia",
        "area_km2": 3355,
    },
    "Somaliland": {
        "iso_alpha2": None,
        "iso_alpha3": "XSL",
        "continent": "Africa",
        "area_km2": 176120,
    },
    "South Ossetia": {
        "iso_alpha2": None,
        "iso_alpha3": "XSO",
        "continent": "Asia",
        "area_km2": 3900,
    },
    "Transnistria": {
        "iso_alpha2": None,
        "iso_alpha3": "XTR",
        "continent": "Europe",
        "area_km2": 4163,
    },
}


# ---------------------------------------------------------
# Переименования стран и территорий
# ---------------------------------------------------------

COUNTRY_NAME_RENAMES = {
    "Palestinian Territory Occupied": "Palestine",
    "South Georgia": "South Georgia and the South Sandwich Islands",
}


# ---------------------------------------------------------
# Страны, исключаемые из countries_final
# ---------------------------------------------------------

EXCLUDED_COUNTRIES_FINAL = {
    "Antarctica",
}