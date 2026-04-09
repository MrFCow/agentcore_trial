# Airline Booking Agent

A standalone Strands agent that provides flight booking services via A2A protocol.

## Overview

- **Port**: 8003
- **Protocol**: A2A (Agent-to-Agent)
- **Framework**: Strands Agents with `A2AServer`

## Capabilities

| Tool | Description |
|------|-------------|
| `search_flights(origin, destination, date)` | Search flights by route |
| `check_availability(flight_id, date)` | Check seat availability |
| `get_price(flight_id, date)` | Get price for a flight on a specific date |
| `book_flight(flight_id, passenger_name, date)` | Book a flight |

## Supported Routes (Bidirectional)

| Route | Base Price |
|-------|------------|
| NYC ↔ LAX | $250 |
| NYC ↔ LHR | $550 |
| NYC ↔ CDG | $500 |
| LAX ↔ LHR | $600 |
| LAX ↔ HKG | $800 |
| LHR ↔ CDG | £180 / €180 |
| LHR ↔ HKG | £700 / €700 |
| CDG ↔ HKG | €750 |

**Weekend surcharge: +15%**

## Running

```bash
# Test mode (no server)
uv run python -m main --test

# Start server
uv run python -m main
```

## Environment Variables

| Variable | Default |
|----------|---------|
| `HOST` | `0.0.0.0` |
| `PORT` | `8003` |
| `OPENAI_BASE_URL` | `http://127.0.0.1:4000/v1` |
| `MODEL_ID` | `nemotron-3-super-120b-a12b` |

## A2A Endpoint

- **Server URL**: `http://localhost:8003/`
- **Agent Card**: `http://localhost:8003/.well-known/agent-card.json`

## Testing with curl

```bash
# Search flights NYC to LHR
curl -s -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "search for flights from NYC to LHR on 2026-04-12"}],
        "messageId": "msg-001",
        "kind": "message"
      }
    }
  }'
```

## Data Store

In-memory store (`tools/store.py`) generates:
- ~30 flights daily (bidirectional across 8 routes)
- Multiple departure times per route
- 7-day seat availability (dynamic, regenerated on restart)

> ⚠️ **Note**: This agent imports from `shared/cities.py` for city definitions, routes, and pricing logic. When deploying to Bedrock AgentCore, either include a copy of `cities.py` in the agent package or ensure the parent `a2a/shared/` directory is in the PYTHONPATH.

## Flight Details

Each route has multiple daily flights with:
- Departure time
- Arrival time (calculated based on duration)
- Airline name (based on route region)
- Dynamic pricing (weekend surcharge)

## Dependencies

```toml
dependencies = [
    "strands-agents[a2a]",
    "bedrock-agentcore",
    "openai",
]
```

## Deployment

Deploy to Bedrock AgentCore Runtime. Update `config.py` to use Bedrock model when deploying.