from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass

from .config import DataConfig
from .seed import (
    ROUTES, FLIGHT_CONFIGS, PASSENGER_SEEDS, BOOKING_SEEDS, FULL_FLIGHT_SEED,
    CAPACITY, BASE_PRICES, CANCEL_FEES,
)
from .store import Flight, FlightDataStore, Route, Passenger, Booking, FareClass, FareRule


@dataclass
class BuilderOptions:
    reference_date: Optional[datetime] = None
    days_forward: int = 30
    seed_bookings: bool = True
    include_full_flight: bool = True


class FlightDataStoreBuilder:
    def __init__(self, options: BuilderOptions = None):
        self.options = options or BuilderOptions()
        self._reference_date: Optional[datetime] = None

    def build(self) -> FlightDataStore:
        self._reference_date = (
            self.options.reference_date
            or DataConfig.get_reference_date()
        )

        store = FlightDataStore()
        store.routes = self._build_routes()
        store.flights = self._build_flights()
        store.passengers = self._build_passengers()

        if self.options.seed_bookings:
            store.bookings = self._build_bookings(store.flights)

        return store

    def _build_routes(self) -> Dict[str, Route]:
        return {
            r.id: Route(id=r.id, origin=r.origin, destination=r.destination, distance_km=r.distance_km)
            for r in ROUTES
        }

    def _build_flights(self) -> Dict[str, Flight]:
        flights = {}
        flight_configs_with_days = self._expand_configs_with_days()

        for config in flight_configs_with_days:
            departure = (self._get_reference_date() + timedelta(days=config.day_offset)).replace(hour=config.departure_hour)
            arrival = departure + timedelta(hours=config.flight_duration_hours)

            route = next(r for r in ROUTES if r.id == config.route_id)
            is_long_haul = route.destination in ("NRT", "LHR")
            base_price = BASE_PRICES["ECONOMY"] if is_long_haul else BASE_PRICES["ECONOMY"]

            fare_classes = {
                "ECONOMY": FareClass(
                    class_type="ECONOMY",
                    base_price=base_price,
                    seats_available=CAPACITY["ECONOMY"],
                    fare_rules=FareRule(refundable=True, cancel_fee=CANCEL_FEES["ECONOMY"])
                ),
                "BUSINESS": FareClass(
                    class_type="BUSINESS",
                    base_price=BASE_PRICES["BUSINESS"],
                    seats_available=CAPACITY["BUSINESS"],
                    fare_rules=FareRule(refundable=True, cancel_fee=CANCEL_FEES["BUSINESS"])
                ),
                "FIRST": FareClass(
                    class_type="FIRST",
                    base_price=BASE_PRICES["FIRST"],
                    seats_available=CAPACITY["FIRST"],
                    fare_rules=FareRule(refundable=True, cancel_fee=CANCEL_FEES["FIRST"])
                ),
            }

            flight = Flight(
                id=config.flight_id,
                route_id=config.route_id,
                airline=config.airline,
                departure_time=departure,
                arrival_time=arrival,
                aircraft=config.aircraft,
                fare_classes=fare_classes,
            )
            flights[flight.id] = flight

        if self.options.include_full_flight:
            full = self._create_full_flight()
            if full:
                flights[full.id] = full

        return flights

    def _expand_configs_with_days(self):
        expanded = []
        for config in FLIGHT_CONFIGS:
            for day in range(self.options.days_forward):
                date_str = (self._get_reference_date() + timedelta(days=day)).strftime("%Y%m%d")
                expanded.append(_FlightConfigWithDay(
                    flight_id=f"{config.flight_id}_{date_str}",
                    route_id=config.route_id,
                    airline=config.airline,
                    departure_hour=config.departure_hour,
                    flight_duration_hours=config.flight_duration_hours,
                    aircraft=config.aircraft,
                    day_offset=day,
                ))
        return expanded

    def _create_full_flight(self) -> Optional[Flight]:
        if not self.options.include_full_flight:
            return None

        first_day = self._get_reference_date()
        route = FULL_FLIGHT_SEED["route_id"]
        airline = "British Airways"
        departure = first_day.replace(hour=20)
        arrival = departure + timedelta(hours=7)

        fare_classes = {
            "ECONOMY": FareClass(
                class_type="ECONOMY",
                base_price=BASE_PRICES["ECONOMY"],
                seats_available=0,
                fare_rules=FareRule(refundable=True, cancel_fee=CANCEL_FEES["ECONOMY"])
            ),
            "BUSINESS": FareClass(
                class_type="BUSINESS",
                base_price=BASE_PRICES["BUSINESS"],
                seats_available=CAPACITY["BUSINESS"],
                fare_rules=FareRule(refundable=True, cancel_fee=CANCEL_FEES["BUSINESS"])
            ),
            "FIRST": FareClass(
                class_type="FIRST",
                base_price=BASE_PRICES["FIRST"],
                seats_available=CAPACITY["FIRST"],
                fare_rules=FareRule(refundable=True, cancel_fee=CANCEL_FEES["FIRST"])
            ),
        }

        return Flight(
            id=FULL_FLIGHT_SEED["flight_id"],
            route_id=route,
            airline=airline,
            departure_time=departure,
            arrival_time=arrival,
            aircraft="Airbus A380",
            fare_classes=fare_classes,
        )

    def _build_passengers(self) -> Dict[str, Passenger]:
        return {
            p["id"]: Passenger(
                id=p["id"],
                name=p["name"],
                passport_number=p["passport"],
                email=p["email"],
                phone=p["phone"],
            )
            for p in PASSENGER_SEEDS
        }

    def _build_bookings(self, flights: Dict[str, Flight] = None) -> Dict[str, Booking]:
        bookings = {}

        for i, seed in enumerate(BOOKING_SEEDS):
            passenger_idx = i % len(PASSENGER_SEEDS)
            passenger = PASSENGER_SEEDS[passenger_idx]

            first_day = self._get_reference_date()
            created_at = first_day - timedelta(days=seed.days_before_reference)
            updated_at = created_at

            if seed.status == "CANCELLED":
                created_at = first_day - timedelta(days=seed.days_before_reference + 7)
                updated_at = first_day - timedelta(days=1)
            elif seed.status == "CHANGED":
                updated_at = first_day - timedelta(days=1)

            base_price = BASE_PRICES[seed.fare_class]
            if seed.is_non_refundable:
                total_paid = base_price * 0.9
            else:
                total_paid = base_price

            flight_id = f"{seed.flight_id}_{first_day.strftime('%Y%m%d')}"

            booking = Booking(
                id=seed.id,
                passenger_id=passenger["id"],
                passenger_name=passenger["name"],
                passenger_passport=passenger["passport"],
                passenger_email=passenger["email"],
                flight_id=flight_id,
                fare_class=seed.fare_class,
                status=seed.status,
                total_paid=total_paid,
                created_at=created_at,
                updated_at=updated_at,
            )
            bookings[booking.id] = booking

            if seed.status == "CONFIRMED" and flights and flight_id in flights:
                flight = flights[flight_id]
                if seed.fare_class in flight.fare_classes:
                    flight.fare_classes[seed.fare_class].seats_available -= 1

        return bookings

    def _get_reference_date(self) -> datetime:
        return self._reference_date


class _FlightConfigWithDay:
    def __init__(self, flight_id: str, route_id: str, airline: str, departure_hour: int, flight_duration_hours: int, aircraft: str, day_offset: int):
        self.flight_id = flight_id
        self.route_id = route_id
        self.airline = airline
        self.departure_hour = departure_hour
        self.flight_duration_hours = flight_duration_hours
        self.aircraft = aircraft
        self.day_offset = day_offset