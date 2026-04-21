from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class RouteSeed:
    id: str
    origin: str
    destination: str
    distance_km: int


@dataclass(frozen=True)
class FlightConfig:
    flight_id: str
    route_id: str
    airline: str
    departure_hour: int
    flight_duration_hours: int
    aircraft: str


@dataclass(frozen=True)
class BookingSeed:
    id: str
    flight_id: str
    route_id: str
    fare_class: str
    status: str
    days_before_reference: int
    is_non_refundable: bool = False


ROUTES: List[RouteSeed] = [
    # Outbound
    RouteSeed(id="route_sfo_nrt", origin="SFO", destination="NRT", distance_km=5400),
    RouteSeed(id="route_jfk_lhr", origin="JFK", destination="LHR", distance_km=5500),
    RouteSeed(id="route_lax_cdg", origin="LAX", destination="CDG", distance_km=5900),
    RouteSeed(id="route_ord_dxb", origin="ORD", destination="DXB", distance_km=7800),
    RouteSeed(id="route_mia_gru", origin="MIA", destination="GRU", distance_km=7200),
    # Return (different routes for round-trip)
    RouteSeed(id="route_nrt_sfo", origin="NRT", destination="SFO", distance_km=5400),
    RouteSeed(id="route_lhr_jfk", origin="LHR", destination="JFK", distance_km=5500),
    RouteSeed(id="route_cdg_lax", origin="CDG", destination="LAX", distance_km=5900),
    RouteSeed(id="route_dxb_ord", origin="DXB", destination="ORD", distance_km=7800),
    RouteSeed(id="route_gru_mia", origin="GRU", destination="MIA", distance_km=7200),
]


FLIGHT_CONFIGS: List[FlightConfig] = [
    # Outbound flights
    FlightConfig("BA123", "route_sfo_nrt", "British Airways", 10, 8, "Boeing 777"),
    FlightConfig("BA124", "route_sfo_nrt", "British Airways", 14, 8, "Boeing 787"),
    FlightConfig("UA801", "route_sfo_nrt", "United Airlines", 8, 8, "Airbus A350"),
    FlightConfig("JL002", "route_sfo_nrt", "Japan Airlines", 12, 8, "Boeing 767"),
    FlightConfig("AA100", "route_jfk_lhr", "American Airlines", 18, 7, "Boeing 777"),
    FlightConfig("BA178", "route_jfk_lhr", "British Airways", 20, 7, "Airbus A380"),
    FlightConfig("VS004", "route_jfk_lhr", "Virgin Atlantic", 22, 7, "Airbus A330"),
    FlightConfig("AF067", "route_lax_cdg", "Air France", 15, 8, "Airbus A380"),
    FlightConfig("UA981", "route_lax_cdg", "United Airlines", 19, 8, "Boeing 777"),
    FlightConfig("EK215", "route_ord_dxb", "Emirates", 23, 9, "Boeing 777"),
    FlightConfig("QR726", "route_ord_dxb", "Qatar Airways", 21, 9, "Airbus A350"),
    FlightConfig("LA2456", "route_mia_gru", "LATAM Airlines", 17, 8, "Boeing 767"),
    # Return flights (different hours)
    FlightConfig("JL123", "route_nrt_sfo", "Japan Airlines", 14, 8, "Boeing 767"),
    FlightConfig("JL124", "route_nrt_sfo", "Japan Airlines", 18, 8, "Boeing 787"),
    FlightConfig("UA802", "route_nrt_sfo", "United Airlines", 10, 8, "Airbus A350"),
    FlightConfig("BA125", "route_lhr_jfk", "British Airways", 12, 7, "Airbus A380"),
    FlightConfig("BA179", "route_lhr_jfk", "British Airways", 16, 7, "Airbus A380"),
    FlightConfig("VS005", "route_lhr_jfk", "Virgin Atlantic", 20, 7, "Airbus A330"),
    FlightConfig("AF068", "route_cdg_lax", "Air France", 11, 9, "Airbus A380"),
    FlightConfig("UA982", "route_cdg_lax", "United Airlines", 15, 9, "Boeing 777"),
    FlightConfig("EK216", "route_dxb_ord", "Emirates", 16, 10, "Boeing 777"),
    FlightConfig("QR727", "route_dxb_ord", "Qatar Airways", 22, 10, "Airbus A350"),
    FlightConfig("LA2457", "route_gru_mia", "LATAM Airlines", 19, 9, "Boeing 767"),
    FlightConfig("LA2458", "route_gru_mia", "LATAM Airlines", 23, 9, "Boeing 767"),
]


CAPACITY = {
    "ECONOMY": 20,
    "BUSINESS": 8,
    "FIRST": 4,
}


BASE_PRICES: Dict[str, int] = {
    "ECONOMY": 600,
    "BUSINESS": 1800,
    "FIRST": 3600,
}


CANCEL_FEES: Dict[str, float] = {
    "ECONOMY": 50.0,
    "BUSINESS": 100.0,
    "FIRST": 150.0,
}


PASSENGER_SEEDS: List[Dict[str, str]] = [
    {"id": "p1", "name": "John Chen", "passport": "E12345678", "email": "john.chen@email.com", "phone": "+1-555-0101"},
    {"id": "p2", "name": "Sarah Smith", "passport": "G87654321", "email": "sarah.smith@email.com", "phone": "+1-555-0102"},
    {"id": "p3", "name": "Mike Johnson", "passport": "K11223344", "email": "mike.j@email.com", "phone": "+1-555-0103"},
    {"id": "p4", "name": "Emma Wilson", "passport": "P99887766", "email": "emma.w@email.com", "phone": "+1-555-0104"},
    {"id": "p5", "name": "David Lee", "passport": "A55667788", "email": "david.lee@email.com", "phone": "+1-555-0105"},
]


BOOKING_SEEDS: List[BookingSeed] = [
    BookingSeed("B1", "BA123", "route_sfo_nrt", "BUSINESS", "CONFIRMED", days_before_reference=5, is_non_refundable=False),
    BookingSeed("B2", "AA100", "route_jfk_lhr", "ECONOMY", "CONFIRMED", days_before_reference=3, is_non_refundable=False),
    BookingSeed("B3", "UA801", "route_sfo_nrt", "BUSINESS", "CONFIRMED", days_before_reference=2, is_non_refundable=False),
    BookingSeed("B4", "BA178", "route_jfk_lhr", "FIRST", "CANCELLED", days_before_reference=10, is_non_refundable=False),
    BookingSeed("BOOKING5", "AF067", "route_lax_cdg", "FIRST", "CHANGED", days_before_reference=7, is_non_refundable=False),
    BookingSeed("B6", "BA178", "route_jfk_lhr", "ECONOMY", "CONFIRMED", days_before_reference=3, is_non_refundable=False),
    BookingSeed("B7", "VS004", "route_jfk_lhr", "BUSINESS", "CONFIRMED", days_before_reference=5, is_non_refundable=True),
]


FULL_FLIGHT_SEED = {
    "flight_id": "BA178",
    "route_id": "route_jfk_lhr",
    "fare_class": "ECONOMY",
}