# Multi-turn Evaluation

This guide covers multi-turn conversation evaluation for the Flight Sales Agent.

## Overview

Multi-turn evaluation tests the agent's ability to maintain context across multiple conversation turns and complete complex workflows that require user clarification.

## What is Multi-turn Eval?

```
Single-turn:     User → Agent response
Multi-turn:      User → Agent → User → Agent → User → Agent
                  (continues conversation with context)
```

## Implemented Components

### Session Management

```python
from strands.session import FileSessionManager
from strands_evals.telemetry import StrandsEvalsTelemetry
from strands_evals.mappers import StrandsInMemorySessionMapper
```

### Test Cases (3 implemented)

| Case | Description | Turns |
|------|-------------|-------|
| TC-M1 | Incomplete booking - needs clarification | ["San Francisco", "Next week"] |
| TC-M2 | Booking with missing info | ["SFO to NRT", "E12345678, John", "1234"] |
| TC-M3 | Cancel after policy check | ["ABC123"] |

## Running Multi-turn Eval

Multi-turn cases are included in the main eval runner. No separate command needed:

```bash
# Default: runs all 16 cases including 3 multi-turn cases
uv run python -m eval.run_eval --manual --output eval_results.json

# Or with LLM judge
uv run python -m eval.run_eval --output eval_results.json
```

The runner automatically detects multi-turn cases by:
- Case name starting with "TC-M"
- Metadata containing "turns" key

## How It Works

### 1. Session Manager

Creates persistent sessions that store conversation history:

```python
session_manager = FileSessionManager(
    session_id=session_id,
    storage_dir="eval/sessions"
)
```

### 2. Trace Attributes

Tags spans with session ID to prevent mixing:

```python
agent = Agent(
    ...
    trace_attributes={
        "gen_ai.conversation.id": session_id,
        "session.id": session_id,
    }
)
```

### 3. Multi-turn Task Function

Handles conversation loop:

```python
def get_response_multiturn(case):
    # First turn
    result = agent(case.input)
    # Additional turns
    for turn_input in turns:
        result = agent(turn_input, session_id=session_id)
    return {"output": ..., "trajectory": ..., "session_id": ...}
```

### 4. Telemetry + Session Mapping

For trace-based evaluators:

```python
telemetry = StrandsEvalsTelemetry().setup_in_memory_exporter()
finished_spans = telemetry.in_memory_exporter.get_finished_spans()
mapper = StrandsInMemorySessionMapper()
session = mapper.map_to_session(finished_spans, session_id=session_id)
```

## Current Results

Sample test with TC-M1-incomplete-booking:
- Input: "I want to fly to Tokyo"
- Turns: ["San Francisco", "Next week"]
- Session ID: Generated
- Trajectory: Extracted tool calls preserved

The API is slow (each multi-turn case takes ~30s), so evaluation runs slowly.

## Adding More Test Cases

Edit `eval/experiment.py`:

```python
Case(
    name="TC-M4-new-case",
    input="Initial user message",
    expected_trajectory=["first_tool"],
    metadata={
        "turns": ["second turn", "third turn"],
    }
)
```

## Limitations

- **API latency**: Multi-turn eval is slow due to model API speed
- **ActorSimulator**: Not yet implemented (future enhancement)
- **Full trace-based eval**: Needs more testing with HelpfulnessEvaluator