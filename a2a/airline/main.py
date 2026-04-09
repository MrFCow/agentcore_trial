import os
import sys
import json
from strands import Agent
from strands import tool
from strands.multiagent.a2a import A2AServer
from config import create_model
from tools.store import AirlineStore

store = AirlineStore()

SYSTEM_PROMPT = """You are an Airline Booking Agent.

## Available Routes:
- NYC ↔ LAX, NYC ↔ LHR, NYC ↔ CDG
- LAX ↔ LHR, LAX ↔ HKG
- LHR ↔ CDG, LHR ↔ HKG
- CDG ↔ HKG

## Available Tools:
1. search_flights(origin, destination, date) - Search for flights by origin and destination city codes (NYC/LAX/LHR/CDG/HKG), optional date (YYYY-MM-DD)
2. check_availability(flight_id, date) - Check available seats on a flight for a given date
3. get_price(flight_id, date) - Get the price for a flight for a given date
4. book_flight(flight_id, passenger_name, date) - Book a flight for a passenger for a specific date

## Guidelines:
- Always provide flight details (times, duration) to the user
- Confirm booking details before completing
- If no seats available, suggest alternatives"""


@tool
def search_flights(
    origin: str | None = None, destination: str | None = None, date: str | None = None
) -> str:
    """Search for available flights by origin and destination."""
    results = store.search_flights(origin, destination, date)
    return json.dumps(results, indent=2)


@tool
def check_availability(flight_id: str, date: str) -> str:
    """Check available seats on a flight for a specific date."""
    result = store.check_availability(flight_id, date)
    return json.dumps(result)


@tool
def get_price(flight_id: str, date: str) -> str:
    """Get the price for a flight for a specific date."""
    result = store.get_price(flight_id, date)
    return json.dumps(result)


@tool
def book_flight(flight_id: str, passenger_name: str, date: str) -> str:
    """Book a flight for a specific date."""
    result = store.book_flight(flight_id, passenger_name, date)
    return json.dumps(result)


def test_store():
    """Quick test of the store without starting the server."""
    print("Testing AirlineStore...")

    print("\n1. Search all flights NYC to LHR:")
    print(json.dumps(store.search_flights("NYC", "LHR"), indent=2)[:500])

    print("\n2. Search all flights to HKG:")
    print(json.dumps(store.search_flights(destination="HKG"), indent=2)[:500])

    from datetime import date

    today = date.today().isoformat()
    print(f"\n3. Check availability for FL001 on {today}:")
    print(store.check_availability("FL001", today))

    print(f"\n4. Book flight FL001 for John Doe on {today}:")
    print(store.book_flight("FL001", "John Doe", today))

    print("\n✅ Store tests passed!")


model = create_model()

agent = Agent(
    model=model,
    name="Airline Booking Agent",
    description="An airline booking agent that can search flights by route, check availability, get prices, and book flights.",
    system_prompt=SYSTEM_PROMPT,
    tools=[search_flights, check_availability, get_price, book_flight],
)

a2a_server = A2AServer(agent=agent)

host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "8003"))

if __name__ == "__main__":
    if "--test" in sys.argv:
        test_store()
    else:
        print(f"Starting Airline Agent on {host}:{port}")
        a2a_server.serve(host=host, port=port)
