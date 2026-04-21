from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class FareRule:
    refundable: bool = True
    change_fee: float = 0.0
    cancel_fee: float = 0.0
    min_stay_days: int = 0
    max_stay_days: int = 365


@dataclass
class FareClass:
    class_type: str
    base_price: float
    seats_available: int
    fare_rules: FareRule = field(default_factory=FareRule)


@dataclass
class Flight:
    id: str
    route_id: str
    airline: str
    departure_time: datetime
    arrival_time: datetime
    aircraft: str
    fare_classes: Dict[str, FareClass] = field(default_factory=dict)


@dataclass
class Route:
    id: str
    origin: str
    destination: str
    distance_km: int


@dataclass
class Passenger:
    id: str
    name: str
    passport_number: str
    email: str
    phone: str


@dataclass
class Booking:
    id: str
    passenger_id: str
    passenger_name: str
    passenger_passport: str
    passenger_email: str
    flight_id: str
    fare_class: str
    status: str
    total_paid: float
    created_at: datetime
    updated_at: datetime


class FlightDataStore:
    def __init__(self):
        self.routes: Dict[str, Route] = {}
        self.flights: Dict[str, Flight] = {}
        self.passengers: Dict[str, Passenger] = {}
        self.bookings: Dict[str, Booking] = {}