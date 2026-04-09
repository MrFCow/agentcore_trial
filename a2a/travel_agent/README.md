# Travel Orchestrator Agent

A standalone Strands agent that orchestrates travel bookings by delegating to hotel and airline agents via A2A protocol.

## Overview

- **Port**: 8001
- **Protocol**: A2A (Agent-to-Agent)
- **Framework**: Strands Agents with `A2AServer` + `A2AAgent`
- **Dependencies**: Hotel Agent (8002), Airline Agent (8003)

## Capabilities

| Tool | Description |
|------|-------------|
| `search_hotels(city, room_type, date)` | Search hotels via Hotel Agent |
| `book_hotel(room_id, guest_name, date)` | Book hotel via Hotel Agent |
| `search_flights(origin, destination, date)` | Search flights via Airline Agent |
| `book_flight(flight_id, passenger_name, date)` | Book flight via Airline Agent |

## How It Works

The Travel Agent acts as an orchestrator:
1. Receives user request (e.g., "book flight NYC to LHR and hotel in LHR")
2. Determines which sub-agents to call (hotel + airline)
3. Uses `A2AAgent` to invoke Hotel Agent and Airline Agent
4. Aggregates responses and returns to user

## Supported Cities & Routes

**Cities**: NYC, LAX, LHR, CDG, HKG

**Routes**: All 8 bidirectional routes supported by Airline Agent

## Running

```bash
# Test A2A connections (requires hotel + airline running)
uv run python -m main --test

# Start server
uv run python -m main
```

## Environment Variables

| Variable | Default |
|----------|---------|
| `HOST` | `0.0.0.0` |
| `PORT` | `8001` |
| `HOTEL_AGENT_URL` | `http://localhost:8002` |
| `AIRLINE_AGENT_URL` | `http://localhost:8003` |
| `OPENAI_BASE_URL` | `http://127.0.0.1:4000/v1` |
| `MODEL_ID` | `nemotron-3-super-120b-a12b` |

## A2A Endpoint

- **Server URL**: `http://localhost:8001/`
- **Agent Card**: `http://localhost:8001/.well-known/agent-card.json`

## Testing with curl

```bash
# Full travel booking request
curl -s -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "book a flight from NYC to LHR on 2026-04-12 and a deluxe hotel in LHR for 3 nights"}],
        "messageId": "msg-001",
        "kind": "message"
      }
    }
  }'
```

## Architecture

```
User Request
     │
     ▼
┌─────────────────────┐
│  Travel Agent       │──► A2A ──► Hotel Agent (8002)
│  (port 8001)        │──► A2A ──► Airline Agent (8003)
└─────────────────────┘
     │
     ▼
  Aggregated Response
```

## Dependencies

```toml
dependencies = [
    "strands-agents[a2a]",
    "bedrock-agentcore",
    "openai",
]
```

## Deployment Notes

1. Ensure Hotel Agent and Airline Agent are running and accessible
2. Update `HOTEL_AGENT_URL` and `AIRLINE_AGENT_URL` for production URLs
3. Update `config.py` to use Bedrock model when deploying to AgentCore

## Troubleshooting

If travel agent fails to reach sub-agents:
- Check Hotel Agent is running on `HOTEL_AGENT_URL`
- Check Airline Agent is running on `AIRLINE_AGENT_URL`
- Verify network connectivity between agents