# A2A Multi-Agent Travel System

A multi-agent travel booking system with 3 standalone Strands agents communicating via A2A protocol. Each agent can be deployed independently to Bedrock AgentCore Runtime.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Travel Agent (8001)                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Tools: search_hotels, book_hotel, search_flights, book_flight │ │
│  │                                                            A2A  │ │
│  │                              ┌──────────────┐    ┌─────────────┐│ │
│  │                              │ Hotel Agent │    │ Airline     ││ │
│  │                              │   (8002)    │    │ Agent(8003)││ │
│  │                              └──────────────┘    └─────────────┘│ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

- **Travel Agent** (port 8001): Orchestrator that handles user requests and delegates to hotel/airline via A2A
- **Hotel Agent** (port 8002): Hotel booking service with city-based inventory
- **Airline Agent** (port 8003): Flight booking service with route-based inventory

## Communication

- **A2A Protocol**: Uses Strands' built-in A2A support (`A2AServer` + `A2AAgent`)
- **JSON-RPC 2.0**: All communication via standard A2A JSON-RPC messages
- **Agent Card**: Each agent exposes capabilities at `/.well-known/agent-card.json`

## Supported Cities & Routes

### Cities (5)
| Code | City | Airport | Currency |
|------|------|---------|----------|
| NYC | New York | JFK | USD ($) |
| LAX | Los Angeles | LAX | USD ($) |
| LHR | London | LHR | GBP (£) |
| CDG | Paris | CDG | EUR (€) |
| HKG | Hong Kong | HKG | HKD (HK$) |

### Flight Routes (8 bidirectional)
- NYC ↔ LAX, NYC ↔ LHR, NYC ↔ CDG
- LAX ↔ LHR, LAX ↔ HKG
- LHR ↔ CDG, LHR ↔ HKG
- CDG ↔ HKG

## Agent Capabilities

### Travel Agent (`travel_agent/`)
| Tool | Description |
|------|-------------|
| `search_hotels(city, room_type, date)` | Search hotels by city code |
| `book_hotel(room_id, guest_name, date)` | Book a hotel room |
| `search_flights(origin, destination, date)` | Search flights by route |
| `book_flight(flight_id, passenger_name, date)` | Book a flight |

### Hotel Agent (`hotel/`)
| Tool | Description |
|------|-------------|
| `search_rooms(city, room_type, date)` | Search available rooms |
| `check_availability(room_id, date)` | Check room availability |
| `get_price(room_id, date)` | Get room price for date |
| `make_reservation(room_id, guest_name, date)` | Make reservation |

- **Inventory**: 15 hotels (3 per city), 3 room types each (standard/deluxe/suite)
- **Dynamic Pricing**: Weekend +20%

### Airline Agent (`airline/`)
| Tool | Description |
|------|-------------|
| `search_flights(origin, destination, date)` | Search available flights |
| `check_availability(flight_id, date)` | Check seat availability |
| `get_price(flight_id, date)` | Get flight price for date |
| `book_flight(flight_id, passenger_name, date)` | Book a flight |

- **Inventory**: ~30 flights daily across 8 routes (bidirectional)
- **Dynamic Pricing**: Weekend +15%

## Project Structure

```
a2a/
├── README.md                  # This file
├── shared/
│   └── cities.py              # City definitions, pricing logic, routes
├── travel_agent/
│   ├── config.py              # Model configuration (OpenAI-compatible)
│   ├── main.py                # A2A server + travel orchestrator tools
│   └── pyproject.toml
├── hotel/
│   ├── config.py
│   ├── main.py                # A2A server + hotel booking tools
│   ├── tools/
│   │   └── store.py           # HotelStore (in-memory, city-based)
│   └── pyproject.toml
└── airline/
    ├── config.py
    ├── main.py                # A2A server + flight booking tools
    ├── tools/
    │   └── store.py           # AirlineStore (in-memory, route-based)
    └── pyproject.toml
```

> ⚠️ **Note**: The `shared/` folder contains city definitions used by both `hotel` and `airline` agents. When deploying to Bedrock AgentCore, each agent should either include its own copy of `cities.py` or the shared folder should be added to the PYTHONPATH. Future refactoring to duplicate city logic within each agent's `tools/store.py` would simplify independent packaging.

## Quick Start

### Prerequisites
- Python 3.10+
- uv package manager
- OpenAI-compatible API (e.g., LM Studio, Ollama) or Bedrock

### Test Individual Agents
```bash
# Test hotel store
cd a2a/hotel && uv sync && uv run python -m main --test

# Test airline store  
cd a2a/airline && uv sync && uv run python -m main --test
```

### Start All Agents (3 terminals)

**Terminal 1 - Hotel Agent:**
```bash
cd a2a/hotel
uv sync
uv run python -m main
```

**Terminal 2 - Airline Agent:**
```bash
cd a2a/airline
uv sync  
uv run python -m main
```

**Terminal 3 - Travel Agent:**
```bash
cd a2a/travel_agent
uv sync
uv run python -m main
```

### Query via curl
```bash
curl -s -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "book a flight from NYC to LHR 2 days from now and a hotel in LHR for 3 nights"}],
        "messageId": "msg-001",
        "kind": "message"
      }
    }
  }'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_BASE_URL` | OpenAI-compatible API endpoint | `http://127.0.0.1:4000/v1` |
| `OPENAI_API_KEY` | API key | `NA` |
| `MODEL_ID` | Model name | `nemotron-3-super-120b-a12b` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Agent port | 8001/8002/8003 |
| `HOTEL_AGENT_URL` | Hotel agent A2A endpoint | `http://localhost:8002` |
| `AIRLINE_AGENT_URL` | Airline agent A2A endpoint | `http://localhost:8003` |

## Data Model

### Hotels
Each city has 3 hotels with 3 room types:
- **Standard**: Basic amenities (wifi, tv, ac)
- **Deluxe**: + minibar, ocean_view
- **Suite**: + balcony, jacuzzi

### Pricing Matrix

**Hotels (per night, weekday):**
| Room | NYC | LAX | LHR | CDG | HKG |
|------|-----|-----|-----|-----|-----|
| Standard | $150 | $130 | £100 | €110 | HK$900 |
| Deluxe | $280 | $250 | £180 | €190 | HK$1600 |
| Suite | $500 | $450 | £350 | €360 | HK$3000 |

**Flights (one-way, weekday):**
| Route | Price |
|-------|-------|
| NYC-LAX | $250 |
| NYC-LHR | $550 |
| NYC-CDG | $500 |
| LAX-LHR | $600 |
| LAX-HKG | $800 |
| LHR-CDG | £180 / €180 |
| LHR-HKG | £700 / €700 |
| CDG-HKG | €750 |

**Weekend Surcharges:**
- Hotels: +20%
- Flights: +15%

## Deployment to AgentCore

Each agent is designed to deploy independently:

1. **Travel Agent** → AgentCore Runtime (port 8001)
2. **Hotel Agent** → AgentCore Runtime (port 8002)
3. **Airline Agent** → AgentCore Runtime (port 8003)

When deploying to AgentCore, update `config.py` to use Bedrock model instead of OpenAI-compatible endpoint.

## Extending the System

### Adding Cities
Edit `shared/cities.py`:
1. Add city to `CITIES` dict
2. Add hotel base prices to `HOTEL_BASE_PRICES`
3. Add routes in `ROUTES` (airline store auto-generates reverse)

### Changing Data Store
Currently using in-memory stores. To swap:
- Implement persistent store (DB, file)
- Update `HotelStore` / `AirlineStore` class interfaces
- No changes needed to agents - they just call the store methods

### Adding New Tools
1. Add method to store class
2. Wrap with `@tool` decorator in main.py
3. Update system prompt with new tool description
4. Agent automatically exposes via A2A