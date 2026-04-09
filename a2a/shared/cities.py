from dataclasses import dataclass
from enum import Enum


class CityCode(Enum):
    NYC = "NYC"
    LAX = "LAX"
    LHR = "LHR"
    CDG = "CDG"
    HKG = "HKG"


@dataclass
class City:
    code: str
    name: str
    airport: str
    country: str
    region: str
    currency: str
    currency_symbol: str


CITIES = {
    "NYC": City("NYC", "New York", "JFK", "USA", "Americas", "USD", "$"),
    "LAX": City("LAX", "Los Angeles", "LAX", "USA", "Americas", "USD", "$"),
    "LHR": City("LHR", "London", "LHR", "UK", "EMEA", "GBP", "£"),
    "CDG": City("CDG", "Paris", "CDG", "France", "EMEA", "EUR", "€"),
    "HKG": City("HKG", "Hong Kong", "HKG", "China", "APAC", "HKD", "HK$"),
}


CITY_LIST = list(CITIES.values())


def get_city(code: str) -> City | None:
    return CITIES.get(code.upper())


def is_weekend(date_str: str) -> bool:
    """Check if a date falls on a weekend (Sat=5, Sun=6)."""
    from datetime import datetime

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.weekday() >= 5


def format_price(amount: float, currency: str) -> str:
    """Format price with currency symbol."""
    symbols = {"USD": "$", "GBP": "£", "EUR": "€", "HKD": "HK$"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:.0f}"


HOTEL_BASE_PRICES = {
    "NYC": {"standard": 150, "deluxe": 280, "suite": 500},
    "LAX": {"standard": 130, "deluxe": 250, "suite": 450},
    "LHR": {"standard": 100, "deluxe": 180, "suite": 350},
    "CDG": {"standard": 110, "deluxe": 190, "suite": 360},
    "HKG": {"standard": 900, "deluxe": 1600, "suite": 3000},
}

FLIGHT_BASE_PRICES = {
    ("NYC", "LAX"): 250,
    ("LAX", "NYC"): 250,
    ("NYC", "LHR"): 550,
    ("LHR", "NYC"): 550,
    ("NYC", "CDG"): 500,
    ("CDG", "NYC"): 500,
    ("LAX", "LHR"): 600,
    ("LHR", "LAX"): 600,
    ("LAX", "HKG"): 800,
    ("HKG", "LAX"): 800,
    ("LHR", "CDG"): 180,
    ("CDG", "LHR"): 180,
    ("LHR", "HKG"): 700,
    ("HKG", "LHR"): 700,
    ("CDG", "HKG"): 750,
    ("HKG", "CDG"): 750,
}

WEEKEND_HOTEL_MULTIPLIER = 1.20
WEEKEND_FLIGHT_MULTIPLIER = 1.15


def get_hotel_price(city_code: str, room_type: str, is_weekend: bool) -> float:
    base = HOTEL_BASE_PRICES.get(city_code, {}).get(room_type, 100)
    if is_weekend:
        base *= WEEKEND_HOTEL_MULTIPLIER
    return base


def get_flight_price(origin: str, destination: str, is_weekend: bool) -> float:
    key = (origin, destination)
    base = FLIGHT_BASE_PRICES.get(key, 400)
    if is_weekend:
        base *= WEEKEND_FLIGHT_MULTIPLIER
    return base


HOTELS = {
    "NYC": [
        {
            "hotel_id": "nyc_grand",
            "name": "Manhattan Grand",
            "city": "NYC",
            "rating": 4.5,
        },
        {
            "hotel_id": "nyc_times",
            "name": "Times Square Inn",
            "city": "NYC",
            "rating": 4.0,
        },
        {
            "hotel_id": "nyc_brook",
            "name": "Brooklyn Heights Hotel",
            "city": "NYC",
            "rating": 4.2,
        },
    ],
    "LAX": [
        {
            "hotel_id": "lax_grand",
            "name": "LA Grand Hotel",
            "city": "LAX",
            "rating": 4.3,
        },
        {
            "hotel_id": "lax_santa",
            "name": "Santa Monica Bay Hotel",
            "city": "LAX",
            "rating": 4.1,
        },
        {
            "hotel_id": "lax_beverly",
            "name": "Beverly Hills Suites",
            "city": "LAX",
            "rating": 4.6,
        },
    ],
    "LHR": [
        {
            "hotel_id": "lhr_grand",
            "name": "London Grand Hotel",
            "city": "LHR",
            "rating": 4.4,
        },
        {
            "hotel_id": "lhr_regent",
            "name": "Regent Park Hotel",
            "city": "LHR",
            "rating": 4.2,
        },
        {
            "hotel_id": "lhr_kensington",
            "name": "Kensington Palace Hotel",
            "city": "LHR",
            "rating": 4.7,
        },
    ],
    "CDG": [
        {
            "hotel_id": "cdg_grand",
            "name": "Paris Grand Hotel",
            "city": "CDG",
            "rating": 4.3,
        },
        {
            "hotel_id": "cdg_champs",
            "name": "Champs-Élysées Hotel",
            "city": "CDG",
            "rating": 4.5,
        },
        {
            "hotel_id": "cdg_montmartre",
            "name": "Montmartre Residence",
            "city": "CDG",
            "rating": 4.1,
        },
    ],
    "HKG": [
        {
            "hotel_id": "hkg_grand",
            "name": "Hong Kong Grand Hotel",
            "city": "HKG",
            "rating": 4.5,
        },
        {
            "hotel_id": "hkg_victoria",
            "name": "Victoria Peak Hotel",
            "city": "HKG",
            "rating": 4.4,
        },
        {
            "hotel_id": "hkg_kowloon",
            "name": "Kowloon City Hotel",
            "city": "HKG",
            "rating": 4.2,
        },
    ],
}


def get_hotels_for_city(city_code: str) -> list[dict]:
    return HOTELS.get(city_code, [])
