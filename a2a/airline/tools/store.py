import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import json
import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

from shared.cities import (
    CITIES,
    get_city,
    is_weekend,
    get_flight_price,
    FLIGHT_BASE_PRICES,
    format_price,
)


@dataclass
class Flight:
    flight_id: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    base_price: float
    airline: str


ROUTES = {
    ("NYC", "LAX"): [
        {"time": "07:00", "duration": 330},
        {"time": "10:00", "duration": 330},
        {"time": "14:00", "duration": 330},
        {"time": "18:00", "duration": 330},
    ],
    ("NYC", "LHR"): [
        {"time": "20:00", "duration": 420},
        {"time": "22:00", "duration": 420},
        {"time": "18:00", "duration": 420},
    ],
    ("NYC", "CDG"): [
        {"time": "19:00", "duration": 435},
        {"time": "21:00", "duration": 435},
    ],
    ("LAX", "LHR"): [
        {"time": "22:00", "duration": 660},
        {"time": "15:00", "duration": 660},
        {"time": "20:00", "duration": 660},
    ],
    ("LAX", "HKG"): [
        {"time": "23:00", "duration": 900},
        {"time": "11:00", "duration": 900},
    ],
    ("LHR", "CDG"): [
        {"time": "08:00", "duration": 60},
        {"time": "10:00", "duration": 60},
        {"time": "14:00", "duration": 60},
        {"time": "18:00", "duration": 60},
    ],
    ("LHR", "HKG"): [
        {"time": "21:00", "duration": 720},
        {"time": "12:00", "duration": 720},
    ],
    ("CDG", "HKG"): [
        {"time": "23:00", "duration": 780},
    ],
}


class AirlineStore:
    def __init__(self):
        self._flights = self._generate_flights()
        self._availability = self._generate_availability()
        self._bookings = []

    def _generate_flights(self) -> list[Flight]:
        flights = []
        flight_counter = 1

        # Generate flights for both directions of each route
        for (origin, destination), schedule in ROUTES.items():
            # Forward direction
            for flight in schedule:
                flight_id = f"FL{flight_counter:03d}"
                flight_counter += 1

                base_price = FLIGHT_BASE_PRICES.get((origin, destination), 400)

                dep_hour, dep_min = map(int, flight["time"].split(":"))
                arrival_mins = dep_hour * 60 + dep_min + flight["duration"]
                arr_hour = (arrival_mins // 60) % 24
                arr_min = arrival_mins % 60
                arrival_time = f"{arr_hour:02d}:{arr_min:02d}"

                airline = self._get_airline_name(origin, destination)

                flights.append(
                    Flight(
                        flight_id=flight_id,
                        origin=origin,
                        destination=destination,
                        departure_time=flight["time"],
                        arrival_time=arrival_time,
                        base_price=base_price,
                        airline=airline,
                    )
                )

            # Reverse direction
            reverse_key = (destination, origin)
            reverse_base_price = FLIGHT_BASE_PRICES.get(reverse_key, 400)
            for flight in schedule:
                flight_id = f"FL{flight_counter:03d}"
                flight_counter += 1

                # Use same schedule for reverse (simplified)
                dep_hour, dep_min = map(int, flight["time"].split(":"))
                arrival_mins = dep_hour * 60 + dep_min + flight["duration"]
                arr_hour = (arrival_mins // 60) % 24
                arr_min = arrival_mins % 60
                arrival_time = f"{arr_hour:02d}:{arr_min:02d}"

                airline = self._get_airline_name(destination, origin)

                flights.append(
                    Flight(
                        flight_id=flight_id,
                        origin=destination,
                        destination=origin,
                        departure_time=flight["time"],
                        arrival_time=arrival_time,
                        base_price=reverse_base_price,
                        airline=airline,
                    )
                )

        return flights

    def _get_airline_name(self, origin: str, destination: str) -> str:
        if origin in ["NYC", "LAX"]:
            if destination in ["NYC", "LAX"]:
                return "American Air"
            return "TransAtlantic Airways"
        elif origin in ["LHR", "CDG"]:
            if destination in ["LHR", "CDG"]:
                return "European Air"
            return "EuroAsia Airways"
        else:
            return "Asia Pacific Airlines"

    def _generate_availability(self) -> dict:
        """Generate availability for next 7 days. Mark ~20% as sold out."""
        availability = {}
        today = datetime.now().date()

        for i in range(7):
            date = today + timedelta(days=i)
            date_str = date.isoformat()
            availability[date_str] = {}

            for flight in self._flights:
                base_seats = random.randint(20, 60)
                sold_out = random.random() < 0.2
                seats = 0 if sold_out else base_seats
                availability[date_str][flight.flight_id] = seats

        return availability

    def _get_price_for_date(self, flight: Flight, date_str: str) -> float:
        weekend = is_weekend(date_str)
        return get_flight_price(flight.origin, flight.destination, weekend)

    def search_flights(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        date: Optional[str] = None,
    ) -> list[dict]:
        flights = self._flights

        if origin:
            flights = [f for f in flights if f.origin.upper() == origin.upper()]
        if destination:
            flights = [
                f for f in flights if f.destination.upper() == destination.upper()
            ]

        results = []
        for flight in flights:
            entry = {
                "flight_id": flight.flight_id,
                "origin": flight.origin,
                "destination": flight.destination,
                "departure_time": flight.departure_time,
                "arrival_time": flight.arrival_time,
                "airline": flight.airline,
                "price": self._get_price_for_date(
                    flight, date or datetime.now().date().isoformat()
                ),
            }
            if date:
                entry["seats_available"] = self._availability.get(date, {}).get(
                    flight.flight_id, 0
                )
            results.append(entry)
        return results

    def check_availability(self, flight_id: str, date: str) -> dict:
        seats = self._availability.get(date, {}).get(flight_id, 0)
        flight = next((f for f in self._flights if f.flight_id == flight_id), None)
        if not flight:
            return {"error": "Flight not found"}

        return {
            "flight_id": flight_id,
            "date": date,
            "seats_available": seats,
            "price": self._get_price_for_date(flight, date),
        }

    def get_price(self, flight_id: str, date: str) -> dict:
        flight = next((f for f in self._flights if f.flight_id == flight_id), None)
        if not flight:
            return {"error": "Flight not found"}

        city = CITIES.get(flight.origin)
        price = self._get_price_for_date(flight, date)

        return {
            "flight_id": flight_id,
            "date": date,
            "price": price,
            "currency": city.currency if city else "USD",
            "formatted": format_price(price, city.currency if city else "USD"),
        }

    def book_flight(self, flight_id: str, passenger_name: str, date: str) -> dict:
        flight = next((f for f in self._flights if f.flight_id == flight_id), None)
        if not flight:
            return {"status": "failed", "reason": "Flight not found"}

        seats = self._availability.get(date, {}).get(flight_id, 0)
        if seats <= 0:
            return {"status": "failed", "reason": "No seats available on this flight"}

        self._availability[date][flight_id] = seats - 1

        booking_id = (
            f"FLY-{flight_id}-{date.replace('-', '')}-{passenger_name[:4].upper()}"
        )

        self._bookings.append(
            {
                "booking_id": booking_id,
                "flight_id": flight_id,
                "origin": flight.origin,
                "destination": flight.destination,
                "passenger_name": passenger_name,
                "date": date,
                "price": self._get_price_for_date(flight, date),
            }
        )

        return {
            "status": "confirmed",
            "booking_id": booking_id,
            "flight_id": flight_id,
            "origin": flight.origin,
            "destination": flight.destination,
            "departure_time": flight.departure_time,
            "arrival_time": flight.arrival_time,
            "airline": flight.airline,
            "passenger_name": passenger_name,
            "date": date,
            "price": self._get_price_for_date(flight, date),
        }

    def get_available_routes(self) -> list[dict]:
        routes = []
        for (origin, dest), _ in ROUTES.items():
            routes.append({"origin": origin, "destination": dest})
        return routes
