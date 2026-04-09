# A2A Multi-Agent Travel System

A multi-agent travel booking system with 3 standalone Strands agents communicating via A2A protocol.

## Architecture

```
┌─────────────────┐     A2A      ┌──────────────┐     A2A      ┌─────────────┐
│ Travel Agent    │ ──────────> │ Hotel Agent  │              │ Airline     │
│ (port 8001)     │ <─────────  │ (port 8002)  │              │ (port 8003) │
└─────────────────┘              └──────────────┘              └─────────────┘
```

## Supported Cities & Routes

### Cities
| Code | City | Airport |
|------|------|---------|
| NYC | New York | JFK |
| LAX | Los Angeles | LAX |
| LHR | London | LHR |
| CDG | Paris | CDG |
| HKG | Hong Kong | HKG |

### Flight Routes
- NYC ↔ LAX, NYC ↔ LHR, NYC ↔ CDG
- LAX ↔ LHR, LAX ↔ HKG
- LHR ↔ CDG, LHR ↔ HKG
- CDG ↔ HKG

## Agents

### 1. Travel Agent (`travel_agent/`)
- **Port**: 8001
- **Role**: Orchestrator - handles user requests and delegates to hotel/airline
- **Tools**: `search_hotels`, `book_hotel`, `search_flights`, `book_flight`

### 2. Hotel Agent (`hotel/`)
- **Port**: 8002
- **Hotels**: 3 per city (15 total)
- **Room Types**: standard, deluxe, suite
- **Pricing**: Dynamic based on city, room type, and weekend surcharge (+20%)

### 3. Airline Agent (`airline/`)
- **Port**: 8003
- **Flights**: Multiple daily flights per route
- **Pricing**: Dynamic based on route distance and weekend surcharge (+15%)

## Folder Structure

```
a2a/
├── README.md
├── shared/
│   └── cities.py         # City definitions, pricing, weekend logic
├── travel_agent/
│   ├── config.py
│   ├── main.py
│   └── pyproject.toml
├── hotel/
│   ├── config.py
│   ├── main.py
│   ├── tools/store.py    # City-based hotel data
│   └── pyproject.toml
└── airline/
    ├── config.py
    ├── main.py
    ├── tools/store.py    # Route-based flight data
    └── pyproject.toml
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_BASE_URL` | OpenAI-compatible API endpoint | `http://127.0.0.1:4000/v1` |
| `OPENAI_API_KEY` | API key | `NA` |
| `MODEL_ID` | Model name | `nemotron-3-super-120b-a12b` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8001`, `8002`, `8003` |
| `HOTEL_AGENT_URL` | Hotel agent endpoint | `http://localhost:8002` |
| `AIRLINE_AGENT_URL` | Airline agent endpoint | `http://localhost:8003` |

## Running the Agents

### Test Mode (No Server)
```bash
cd a2a/hotel && uv run python -m main --test
cd a2a/airline && uv run python -m main --test
```

### Start Servers (3 terminals)
```bash
# Terminal 1 - Hotel Agent
cd a2a/hotel && uv run python -m main

# Terminal 2 - Airline Agent  
cd a2a/airline && uv run python -m main

# Terminal 3 - Travel Agent
cd a2a/travel_agent && uv run python -m main
```

## Testing with curl

```bash
curl -X POST http://localhost:8001/ \
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

## Data Model

### Hotel Pricing (per night)
| Room Type | NYC | LAX | LHR | CDG | HKG |
|-----------|-----|-----|-----|-----|-----|
| Standard | $150 | £100 | €110 | HK$900 |
| Deluxe | $280 | £180 | €190 | HK$1600 |
| Suite | $500 | £350 | €360 | HK$3000 |
- Weekend surcharge: +20%

### Flight Pricing (one-way)
| Route | Base Price |
|-------|------------|
| NYC-LAX | $250 |
| NYC-LHR | $550 |
| NYC-CDG | $500 |
| LAX-LHR | $600 |
| LAX-HKG | $800 |
| LHR-CDG | $180 |
| LHR-HKG | $700 |
| CDG-HKG | $750 |
- Weekend surcharge: +15%

## Deployment

Each agent deploys independently to Bedrock AgentCore Runtime.