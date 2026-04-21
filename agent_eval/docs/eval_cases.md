# Test Case Definitions

This document describes the test case format and test cases for the Flight Sales Agent evaluation.

## Case Format

Test cases are defined using Strands Evals `Case` class with type annotations:

```python
from strands_evals import Case

case = Case[str, str](
    name="case-name",
    input="user message",
    expected_output="expected response",
    expected_trajectory=["tool_a", "tool_b"],  # For trajectory eval
    metadata={"intent": "book", "expected_tools": [...]}
)
```

## Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique ID (e.g., "TC-001-search") |
| `input` | string | Yes | User input/message |
| `expected_output` | string | No | Expected response |
| `expected_trajectory` | list | No | Expected tool sequence |
| `metadata` | dict | No | Context (intent, etc.) |

## Test Cases (16 total)

### Single-turn Cases (13)

#### Search Cases

| ID | Input | Expected Trajectory |
|----|-------|---------------------|
| TC-001 | "Flights from SFO to Tokyo April 20" | list_routes → search_flights |
| TC-005 | "Flights from XYZ to ABC on Jan 1" | list_routes (edge case) |
| TC-006 | "Show me flights from New York to London" | list_routes → search_flights |
| TC-007 | "Find flights from LAX to Paris on December 25" | list_routes → search_flights |
| TC-011 | "Check availability for BA178 economy" | verify_availability |
| TC-012 | "What routes do you have?" | list_routes |

#### Book Cases

| ID | Input | Expected Trajectory |
|----|-------|---------------------|
| TC-002 | "Book BA123 for John Chen, passport E12345678" | verify_availability → validate_passport → process_payment → issue_ticket → send_confirmation |
| TC-008 | "Book business class SFO to NRT next Friday" | search_flights → verify_availability → validate_passport → process_payment → issue_ticket |
| TC-009 | "Book SFO to NRT, passport ABC12345" | validate_passport (edge case) |

#### Change/Cancel Cases

| ID | Input | Expected Trajectory |
|----|-------|---------------------|
| TC-003 | "Change booking ABC to April 22" | get_booking → check_policy → check_availability → update_booking → send_confirmation |
| TC-004 | "Cancel booking ABC" | get_booking → check_policy → process_refund → cancel_ticket → send_confirmation |

#### Info/Other Cases

| ID | Input | Expected Trajectory |
|----|-------|---------------------|
| TC-010 | "What is change policy for REF123?" | get_booking → check_policy |
| TC-013 | "Tell me a joke" | [] (no tools) |

### Multi-turn Cases (3)

| ID | Description | Input | Turns | Expected |
|----|-------------|-------|-------|----------|
| TC-M1 | Incomplete booking | "I want to fly to Tokyo" | ["San Francisco", "Next week"] | list_routes |
| TC-M2 | Booking with info | "Book a flight" | ["SFO to NRT", "E12345678, John", "1234"] | list_routes → ... |
| TC-M3 | Cancel after policy | "Cancel my booking" | ["ABC123"] | get_booking → ... |

## Expected Workflows

### Search Flow
```
list_routes → search_flights
```

### Book Flow
```
verify_availability → validate_passport → process_payment → issue_ticket → send_confirmation
```

### Change Flow
```
get_booking → check_policy → check_availability → update_booking → send_confirmation
```

### Cancel Flow
```
get_booking → check_policy → process_refund → cancel_ticket → send_confirmation
```

## Running Evaluation

```bash
# Default: LLM judge (async, parallel)
uv run python -m eval.run_eval --output results.json

# Sync mode (sequential)
uv run python -m eval.run_eval --sync --output results.json

# Manual only (rule-based, no LLM)
uv run python -m eval.run_eval --manual --output results.json
```

## Adding Test Cases

1. Edit `eval/experiment.py`
2. Add `Case[str, str]` with `expected_trajectory`
3. Run evaluation:
   ```bash
   uv run python -m eval.run_eval --output results.json
   ```
