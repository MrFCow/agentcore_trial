import os
import sys
import json
from strands import Agent
from strands import tool
from strands.multiagent.a2a import A2AServer
from config import create_model
from tools.store import HotelStore

store = HotelStore()

SYSTEM_PROMPT = """You are a Hotel Booking Agent.

## Available Cities:
NYC (New York), LAX (Los Angeles), LHR (London), CDG (Paris), HKG (Hong Kong)

## Available Tools:
1. search_rooms(city, room_type, date) - Search available rooms by city (NYC/LAX/LHR/CDG/HKG), optional room_type (standard/deluxe/suite), optional date (YYYY-MM-DD)
2. check_availability(room_id, date) - Check if a specific room is available for a given date
3. get_price(room_id, date) - Get the price for a specific room for a given date
4. make_reservation(room_id, guest_name, date) - Make a reservation for a room for a specific date

## Guidelines:
- Always provide clear, concise information to the user
- Confirm reservation details before completing
- If room is not available, suggest alternatives"""


@tool
def search_rooms(
    city: str | None = None, room_type: str | None = None, date: str | None = None
) -> str:
    """Search for available hotel rooms by city."""
    results = store.search_rooms(city, room_type, date)
    return json.dumps(results, indent=2)


@tool
def check_availability(room_id: str, date: str) -> str:
    """Check if a room is available for a specific date."""
    result = store.check_availability(room_id, date)
    return json.dumps(result)


@tool
def get_price(room_id: str, date: str) -> str:
    """Get the price for a room for a specific date."""
    result = store.get_price(room_id, date)
    return json.dumps(result)


@tool
def make_reservation(room_id: str, guest_name: str, date: str) -> str:
    """Make a reservation for a room for a specific date."""
    result = store.make_reservation(room_id, guest_name, date)
    return json.dumps(result)


def test_store():
    """Quick test of the store without starting the server."""
    print("Testing HotelStore...")

    print("\n1. Search all rooms in NYC:")
    print(json.dumps(store.search_rooms("NYC"), indent=2)[:500])

    print("\n2. Search deluxe rooms in London:")
    print(json.dumps(store.search_rooms("LHR", "deluxe"), indent=2)[:500])

    from datetime import date

    today = date.today().isoformat()
    print(f"\n3. Check availability for nyc_grand_standard on {today}:")
    print(store.check_availability("nyc_grand_standard", today))

    print(f"\n4. Make reservation for nyc_grand_standard on {today}:")
    print(store.make_reservation("nyc_grand_standard", "John Doe", today))

    print("\n✅ Store tests passed!")


model = create_model()

agent = Agent(
    model=model,
    name="Hotel Booking Agent",
    description="A hotel booking agent that can search rooms by city, check availability, get prices, and make reservations.",
    system_prompt=SYSTEM_PROMPT,
    tools=[search_rooms, check_availability, get_price, make_reservation],
)

a2a_server = A2AServer(agent=agent)

host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "8002"))

if __name__ == "__main__":
    if "--test" in sys.argv:
        test_store()
    else:
        print(f"Starting Hotel Agent on {host}:{port}")
        a2a_server.serve(host=host, port=port)
