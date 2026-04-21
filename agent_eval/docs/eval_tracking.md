# Transaction History & Trace Tracking

This document outlines the design for capturing and storing transaction history for future evaluation.

## Overview

Transaction history captures real-world agent interactions that can be:
1. Reviewed for debugging
2. Sampled for evaluation
3. Used to detect regressions
4. Fed back into test case generation

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────▶│  Flight Agent   │────▶│  Response       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Trace Capture  │
                        │  (on-the-fly)   │
                        └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │ traces/         │
                        │ (JSONL files)   │
                        └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │ Eval Pipeline   │
                        │ (batch/scheduled)│
                        └─────────────────┘
```

## Trace Schema

Each trace is stored as JSONL with the following structure:

```json
{
  "trace_id": "uuid-string",
  "timestamp": "2025-04-20T10:30:00Z",
  "session_id": "session-uuid",
  "user_input": "Flights from SFO to Tokyo",
  "agent_response": "I'd be happy to help...",
  "tool_calls": [
    {
      "tool": "list_routes",
      "input": {},
      "output": "[routes...]",
      "duration_ms": 120
    },
    {
      "tool": "search_flights",
      "input": {"origin": "SFO", "destination": "NRT"},
      "output": "[flights...]",
      "duration_ms": 350
    }
  ],
  "final_output": {
    "flights": [...],
    "count": 5
  },
  "metadata": {
    "model": "nemotron-3-super-120b-a12b",
    "success": true,
    "error": null
  }
}
```

## Implementation

### 1. Trace Capture (Optional Wrapper)

```python
# eval/trace_capture.py
import uuid
import json
from datetime import datetime
from pathlib import Path

class TraceCapture:
    def __init__(self, output_dir: Path = Path("traces")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def save_trace(self, trace_data: dict):
        trace_id = trace_data.get("trace_id", str(uuid.uuid4()))
        filename = f"trace_{trace_id}.jsonl"
        filepath = self.output_dir / filename
        
        with open(filepath, "w") as f:
            f.write(json.dumps(trace_data, indent=2))
        
        return trace_id
```

### 2. Integration with Agent

Modify `main.py` to optionally capture traces:

```python
# In main.py - optional trace capture
if os.getenv("ENABLE_TRACE_CAPTURE") == "true":
    from eval.trace_capture import TraceCapture
    trace_capture = TraceCapture()
    
    # Wrap agent invocation
    result = await agent.invoke_async(user_input)
    
    trace_data = {
        "trace_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "user_input": user_input,
        "agent_response": str(result),
        "tool_calls": extract_tool_calls(result),
    }
    trace_capture.save_trace(trace_data)
```

### 3. Extract Tool Calls

```python
from strands_evals.extractors import extract_agent_tools_used_from_messages
from strands_evals.extractors import extract_agent_tools_used_from_metrics

def extract_tool_calls(agent_result):
    """Extract tool calls from agent result."""
    # Option 1: from messages
    if hasattr(agent_result, 'messages'):
        return extract_agent_tools_used_from_messages(agent_result.messages)
    
    # Option 2: from metrics
    if hasattr(agent_result, 'metrics'):
        return extract_agent_tools_used_from_metrics(agent_result.metrics)
    
    return []
```

## Usage

### Enable Trace Capture

```bash
# In environment or before running
export ENABLE_TRACE_CAPTURE=true
uv run python main.py
```

### Run Eval on Captured Traces

```python
# Later: evaluate from stored traces
from strands_evals import Experiment
from eval.trace_reader import read_traces

traces = read_traces("traces/")
experiment = Experiment(cases=traces_to_cases(traces))
reports = experiment.run_evaluations(task_function)
```

## Storage Strategy

| Storage | Use Case |
|---------|----------|
| `traces/` (JSONL) | Development, small scale |
| S3 + Athena | Production, large scale |
| Database (PostgreSQL) | Queryable, indexed |

## Retention Policy

- **Development**: Keep last 100 traces
- **Testing**: Keep traces for active eval runs
- **Production**: 30-day rolling window (configurable)

## Privacy Considerations

- [ ] Strip PII from traces before storage
- [ ] Anonymize user identifiers
- [ ] Allow opt-out of trace collection
- [ ] Encrypt traces at rest

## Future Enhancements

- [ ] Real-time eval on sampled traffic
- [ ] Automatic regression detection
- [ ] A/B testing support
- [ ] Dashboard for trace visualization