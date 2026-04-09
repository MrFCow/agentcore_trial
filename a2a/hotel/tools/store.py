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
    get_hotel_price,
    HOTELS,
    get_hotels_for_city,
    format_price,
)


@dataclass
class Room:
    room_id: str
    hotel_id: str
    hotel_name: str
    city: str
    room_type: str
    price: float
    amenities: list[str]


class HotelStore:
    def __init__(self):
        self._rooms = self._generate_rooms()
        self._availability = self._generate_availability()
        self._reservations = []

    def _generate_rooms(self) -> list[Room]:
        rooms = []
        for city_code, hotels in HOTELS.items():
            city = CITIES[city_code]
            for hotel in hotels:
                for room_type in ["standard", "deluxe", "suite"]:
                    base_price = get_hotel_price(city_code, room_type, False)
                    room_id = f"{hotel['hotel_id']}_{room_type}"
                    rooms.append(
                        Room(
                            room_id=room_id,
                            hotel_id=hotel["hotel_id"],
                            hotel_name=hotel["name"],
                            city=city_code,
                            room_type=room_type,
                            price=base_price,
                            amenities=self._get_amenities(room_type),
                        )
                    )
        return rooms

    def _get_amenities(self, room_type: str) -> list[str]:
        common = ["wifi", "tv", "ac"]
        if room_type == "deluxe":
            return common + ["minibar", "ocean_view"]
        elif room_type == "suite":
            return common + ["minibar", "ocean_view", "balcony", "jacuzzi"]
        return common

    def _generate_availability(self) -> dict:
        """Generate availability for next 7 days. Mark ~20% as unavailable."""
        availability = {}
        today = datetime.now().date()

        for i in range(7):
            date = today + timedelta(days=i)
            date_str = date.isoformat()
            availability[date_str] = {}

            for room in self._rooms:
                available = random.random() > 0.2
                availability[date_str][room.room_id] = available

        return availability

    def _get_price_for_date(self, room: Room, date_str: str) -> float:
        weekend = is_weekend(date_str)
        return get_hotel_price(room.city, room.room_type, weekend)

    def search_rooms(
        self,
        city: Optional[str] = None,
        room_type: Optional[str] = None,
        date: Optional[str] = None,
    ) -> list[dict]:
        rooms = self._rooms

        if city:
            rooms = [r for r in rooms if r.city.upper() == city.upper()]
        if room_type:
            rooms = [r for r in rooms if r.room_type.lower() == room_type.lower()]

        results = []
        for room in rooms:
            entry = {
                "room_id": room.room_id,
                "hotel_id": room.hotel_id,
                "hotel_name": room.hotel_name,
                "city": room.city,
                "room_type": room.room_type,
                "price": self._get_price_for_date(
                    room, date or datetime.now().date().isoformat()
                ),
                "amenities": room.amenities,
            }
            if date:
                entry["available"] = self._availability.get(date, {}).get(
                    room.room_id, False
                )
            results.append(entry)
        return results

    def check_availability(self, room_id: str, date: str) -> dict:
        available = self._availability.get(date, {}).get(room_id, False)
        room = next((r for r in self._rooms if r.room_id == room_id), None)
        if not room:
            return {"error": "Room not found"}

        return {
            "room_id": room_id,
            "date": date,
            "available": available,
            "price": self._get_price_for_date(room, date),
            "hotel_name": room.hotel_name,
            "city": room.city,
        }

    def get_price(self, room_id: str, date: str) -> dict:
        room = next((r for r in self._rooms if r.room_id == room_id), None)
        if not room:
            return {"error": "Room not found"}

        city = CITIES.get(room.city)
        price = self._get_price_for_date(room, date)

        return {
            "room_id": room_id,
            "date": date,
            "price": price,
            "currency": city.currency if city else "USD",
            "formatted": format_price(price, city.currency if city else "USD"),
        }

    def make_reservation(self, room_id: str, guest_name: str, date: str) -> dict:
        room = next((r for r in self._rooms if r.room_id == room_id), None)
        if not room:
            return {"status": "failed", "reason": "Room not found"}

        avail = self._availability.get(date, {}).get(room_id)
        if avail is False:
            return {"status": "failed", "reason": "Room not available on this date"}

        if date in self._availability:
            self._availability[date][room_id] = False

        reservation_id = (
            f"RES-{room_id[:8]}-{date.replace('-', '')}-{guest_name[:4].upper()}"
        )

        self._reservations.append(
            {
                "reservation_id": reservation_id,
                "room_id": room_id,
                "hotel_name": room.hotel_name,
                "city": room.city,
                "guest_name": guest_name,
                "date": date,
                "price": self._get_price_for_date(room, date),
            }
        )

        return {
            "status": "confirmed",
            "reservation_id": reservation_id,
            "room_id": room_id,
            "hotel_name": room.hotel_name,
            "city": room.city,
            "guest_name": guest_name,
            "date": date,
            "price": self._get_price_for_date(room, date),
        }

    def get_available_cities(self) -> list[str]:
        return list(CITIES.keys())
