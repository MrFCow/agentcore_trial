# Hotel Booking Agent

A standalone Strands agent that provides hotel booking services via A2A protocol.

## Overview

- **Port**: 8002
- **Protocol**: A2A (Agent-to-Agent)
- **Framework**: Strands Agents with `A2AServer`

## Capabilities

| Tool | Description |
|------|-------------|
| `search_rooms(city, room_type, date)` | Search available rooms by city code |
| `check_availability(room_id, date)` | Check if specific room is available |
| `get_price(room_id, date)` | Get price for a room on a specific date |
| `make_reservation(room_id, guest_name, date)` | Book a room |

## Supported Cities

- **NYC** (New York) - 3 hotels
- **LAX** (Los Angeles) - 3 hotels
- **LHR** (London) - 3 hotels
- **CDG** (Paris) - 3 hotels
- **HKG** (Hong Kong) - 3 hotels

## Room Types

- **standard**: Basic amenities (wifi, tv, ac)
- **deluxe**: + minibar, ocean_view
- **suite**: + balcony, jacuzzi

## Pricing

Base prices (per night, weekday):
| Room Type | NYC | LAX | LHR | CDG | HKG |
|-----------|-----|-----|-----|-----|-----|
| Standard | $150 | $130 | £100 | €110 | HK$900 |
| Deluxe | $280 | $250 | £180 | €190 | HK$1600 |
| Suite | $500 | $450 | £350 | €360 | HK$3000 |

**Weekend surcharge: +20%**

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
| `PORT` | `8002` |
| `OPENAI_BASE_URL` | `http://127.0.0.1:4000/v1` |
| `MODEL_ID` | `nemotron-3-super-120b-a12b` |

## A2A Endpoint

- **Server URL**: `http://localhost:8002/`
- **Agent Card**: `http://localhost:8002/.well-known/agent-card.json`

## Testing with curl

```bash
# Search rooms in NYC
curl -s -X POST http://localhost:8002/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "search for deluxe rooms in NYC for 2026-04-12"}],
        "messageId": "msg-001",
        "kind": "message"
      }
    }
  }'
```

## Data Store

In-memory store (`tools/store.py`) generates:
- 15 hotels (3 per city)
- 45 room types (3 per hotel)
- 7-day availability (dynamic, regenerated on restart)

> ⚠️ **Note**: This agent imports from `shared/cities.py` for city definitions and pricing logic. When deploying to Bedrock AgentCore, either include a copy of `cities.py` in the agent package or ensure the parent `a2a/shared/` directory is in the PYTHONPATH.

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