# Evaluation Quick Start

This guide shows how to run evaluations for the Flight Sales Agent.

## Prerequisites

```bash
cd agent_eval
uv sync
```

## Running Evaluation

### Default: LLM Judge with Async (Recommended)

Uses `local-vllm` as judge model, runs in parallel:

```bash
cd agent_eval
uv run python -m eval.run_eval --output eval_results.json
```

**Features:**
- Uses Strands Evals SDK with `TrajectoryEvaluator` and `OutputEvaluator`
- Model instance from `create_eval_model()` (configurable via `config.py`)
- Runs async (parallel) by default - faster execution
- Results JSON sorted by case name for consistent ordering

### Sync Mode (Sequential)

For debugging - runs one case at a time:

```bash
uv run python -m eval.run_eval --sync --output eval_results.json
```

### Manual Only (No LLM)

Rule-based evaluation - works without model access:

```bash
uv run python -m eval.run_eval --manual --output eval_results.json
```

**Note:** Legacy runners have been consolidated into run_eval.py. Use --manual for rule-based evaluation.

## Test Cases

Current test suite: **16 cases** in `eval/experiment.py`

### Single-turn (13 cases)

| ID | Intent | Expected Trajectory |
|----|--------|-------------------|
| TC-001 | search | list_routes → search_flights |
| TC-002 | book | verify → validate → payment → issue → confirm |
| TC-003 | change | get_booking → check_policy → check → update → confirm |
| TC-004 | cancel | get_booking → check_policy → refund → cancel → confirm |
| TC-005 | search (edge) | list_routes |
| TC-006 | search JFK→LHR | list_routes → search_flights |
| TC-007 | search LAX→CDG | list_routes → search_flights |
| TC-008 | book business | search → verify → validate → payment → issue |
| TC-009 | book invalid passport | validate_passport |
| TC-010 | check policy | get_booking → check_policy |
| TC-011 | verify availability | verify_availability |
| TC-012 | list routes | list_routes |
| TC-013 | off-topic | (no tools) |

### Multi-turn (3 cases)

| ID | Description | Turns |
|----|-------------|-------|
| TC-M1 | Incomplete booking | "I want to fly to Tokyo" → "San Francisco" → "Next week" |
| TC-M2 | Booking with info | "Book a flight" → "SFO to NRT" → "E12345678, John" → "1234" |
| TC-M3 | Cancel after policy | "Cancel my booking" → "ABC123" |

## How It Works

### Architecture

```
run_eval.py
├── create_evaluators()     # Creates TrajectoryEvaluator + OutputEvaluator with model
├── task_function()          # Runs agent, extracts output + trajectory
├── Experiment.run_evaluations_async()  # Runs all cases in parallel
└── Fallback                 # On LLM failure, uses manual evaluation
```

### Model Configuration

In `config.py`:

```python
def create_eval_model():
    client = AsyncOpenAI(
        api_key=os.getenv("EVAL_MODEL_API_KEY", "NA"),
        base_url=os.getenv("EVAL_MODEL_BASE_URL", "http://127.0.0.1:4000/v1"),
    )
    return OpenAIModel(
        client=client,
        model_id=os.getenv("EVAL_MODEL_ID", "local-vllm"),
    )
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_ID` | local-vllm | Agent model |
| `EVAL_MODEL_ID` | local-vllm | Judge model |
| `OPENAI_BASE_URL` | http://127.0.0.1:4000/v1 | API endpoint |
| `OPENAI_API_KEY` | NA | API key (often not needed for local models) |

### Fallback Behavior

When LLM judge fails (timeout, API error, validation error):

```
[FALLBACK] Case TC-002-book-flight: LLM failed, using manual eval
```

Manual evaluation uses rule-based scoring:
- Exact match: 1.0
- Partial match: 0.5 (some tools present)
- No match: 0.0

## Scoring

| Score | Meaning |
|-------|---------|
| 1.0 | Exact match - all expected tools in correct order |
| 0.5-0.8 | Partial - some tools present or wrong order |
| 0.0 | No match - wrong or missing tools |

## Output Format

Results saved to JSON:

```json
[
  {
    "case_name": "TC-001-search-flights",
    "input": "Flights from SFO to Tokyo April 20",
    "expected_tools": ["list_routes", "search_flights"],
    "actual_tools": ["list_routes", "search_flights"],
    "trajectory_score": 1.0,
    "trajectory_reason": "Exact match",
    "output_score": 1.0,
    "method": "llm_judge"  // or "manual_fallback"
  }
]
```

## Adding Test Cases

Edit `eval/experiment.py`:

```python
Case[str, str](
    name="TC-014-new-case",
    input="Your test input",
    expected_output="Expected response",
    expected_trajectory=["tool_a", "tool_b"],
    metadata={"intent": "search"}
)
```

## Current Results (Manual Mode)

```
===============================================================
SUMMARY
===============================================================
Trajectory: 10/16 (62%)
Method: manual
```

**Note:** The 62% trajectory score is expected because:
- Search/list routes cases: 100% pass
- Booking/change/cancel cases: Agent asks clarifying questions instead of completing full workflow
- Multi-turn cases all passed (TC-M1, TC-M2, TC-M3)

## Multi-turn Evaluation

See `docs/eval_multiturn.md` for multi-turn test case setup.
