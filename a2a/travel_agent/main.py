import os
import sys
import json
from datetime import date
from strands import Agent
from strands import tool
from strands.agent.a2a_agent import A2AAgent
from strands.multiagent.a2a import A2AServer
from config import create_model

hotel_agent_url = os.getenv("HOTEL_AGENT_URL", "http://localhost:8002")
airline_agent_url = os.getenv("AIRLINE_AGENT_URL", "http://localhost:8003")

hotel_agent = A2AAgent(endpoint=hotel_agent_url, name="hotel")
airline_agent = A2AAgent(endpoint=airline_agent_url, name="airline")

SYSTEM_PROMPT = """You are a Travel Orchestrator Agent.

## Available Cities:
NYC (New York), LAX (Los Angeles), LHR (London), CDG (Paris), HKG (Hong Kong)

## Available Routes:
- NYC ↔ LAX, NYC ↔ LHR, NYC ↔ CDG
- LAX ↔ LHR, LAX ↔ HKG
- LHR ↔ CDG, LHR ↔ HKG
- CDG ↔ HKG

## Available Tools:
1. search_hotels(city, room_type, date) - Search for available hotel rooms by city code (NYC/LAX/LHR/CDG/HKG)
2. book_hotel(room_id, guest_name, date) - Book a hotel room for a specific date
3. search_flights(origin, destination, date) - Search for flights by origin and destination city codes
4. book_flight(flight_id, passenger_name, date) - Book a flight for a specific date

## Guidelines:
- Understand user needs (destination, dates, preferences)
- Search hotel and airline agents as needed
- Provide comprehensive travel options
- Confirm all booking details before finalizing
- Always include prices in your responses"""


@tool
def search_hotels(
    city: str | None = None, room_type: str | None = None, date: str | None = None
) -> str:
    """Search for hotels via Hotel Agent by city."""
    query = f"Search for rooms"
    if city:
        query += f" in {city}"
    if room_type:
        query += f" of type {room_type}"
    if date:
        query += f" for date {date}"
    result = hotel_agent(query)
    return str(result.message)


@tool
def book_hotel(room_id: str, guest_name: str, date: str) -> str:
    """Book a hotel room via Hotel Agent."""
    result = hotel_agent(
        f"Make reservation for room {room_id} for guest {guest_name} on date {date}"
    )
    return str(result.message)


@tool
def search_flights(
    origin: str | None = None, destination: str | None = None, date: str | None = None
) -> str:
    """Search for flights via Airline Agent by origin and destination."""
    query = f"Search for flights"
    if origin:
        query += f" from {origin}"
    if destination:
        query += f" to {destination}"
    if date:
        query += f" on {date}"
    result = airline_agent(query)
    return str(result.message)


@tool
def book_flight(flight_id: str, passenger_name: str, date: str) -> str:
    """Book a flight via Airline Agent."""
    result = airline_agent(
        f"Book flight {flight_id} for passenger {passenger_name} on date {date}"
    )
    return str(result.message)


def test_agent():
    """Quick test of A2A connections."""
    print("Testing Travel Agent A2A connections...")

    today = date.today().isoformat()

    print(f"\n1. Testing Hotel Agent - search rooms in NYC:")
    try:
        result = hotel_agent(f"Search for rooms in NYC for {today}")
        print(f"   Response: {result.message}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print(f"\n2. Testing Airline Agent - search flights NYC to LHR:")
    try:
        result = airline_agent(f"Search for flights from NYC to LHR for {today}")
        print(f"   Response: {result.message}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n✅ A2A connection tests done!")


model = create_model()

agent = Agent(
    model=model,
    name="Travel Orchestrator Agent",
    description="A travel orchestrator agent that helps plan and book travel including hotels and flights by city.",
    system_prompt=SYSTEM_PROMPT,
    tools=[search_hotels, book_hotel, search_flights, book_flight],
)

a2a_server = A2AServer(agent=agent)

host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "8001"))

if __name__ == "__main__":
    if "--test" in sys.argv:
        test_agent()
    else:
        print(f"Starting Travel Agent on {host}:{port}")
        print(f"Hotel Agent URL: {hotel_agent_url}")
        print(f"Airline Agent URL: {airline_agent_url}")
        a2a_server.serve(host=host, port=port)
