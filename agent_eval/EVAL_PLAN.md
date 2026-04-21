# Flight Sales Agent - Evaluation Plan

## Overview

This document outlines the evaluation approach for the Flight Sales Agent built with Strands Agents SDK.

**Agent**: Flight Sales Agent (booking, search, change, cancel flights)  
**Framework**: Strands Agents + Strands Evals SDK  
**Scope**: Single agent evaluation (not multi-agent)

---

## 1. What to Evaluate

Prioritized in order:

| Priority | Aspect | What it measures | Evaluator |
|----------|--------|------------------|-----------|
| 1 | **Goal Completion** | Did user achieve their intent? | `GoalSuccessRateEvaluator` |
| 2 | **Trajectory** | Correct tool sequence used? | `TrajectoryEvaluator` |
| 3 | **Safety** | Refused harmful requests? | `OutputEvaluator` (custom rubric) |
| 4 | **Helpfulness** | Was agent friendly + clarifying? | `HelpfulnessEvaluator` |

### 1.1 Goal Completion
- Did the agent successfully book a flight when requested?
- Did search return valid results?
- Did change/cancel complete properly?

### 1.2 Trajectory
- Search: `list_routes` → `search_flights`
- Book: `verify_availability` → `validate_passport` → `process_payment` → `issue_ticket` → `send_confirmation`
- Change: `get_booking` → `check_policy` → `check_availability` → `update_booking` → `send_confirmation`
- Cancel: `get_booking` → `check_policy` → `process_refund` → `cancel_ticket` → `send_confirmation`

### 1.3 Safety
- Refuse bookings with invalid passport format
- Refuse suspicious requests (fraud, illegal routes)
- Handle edge cases gracefully

### 1.4 Helpfulness
- Ask clarifying questions when info missing
- Provide clear confirmations
- Explain pricing/policies

---

## 2. Test Case Approach

### 2.1 Initial Set: Manual + LLM-assisted Hybrid

| Phase | Method | Count | Description |
|-------|--------|-------|-------------|
| Phase 1 | Manual | 10-15 | Core cases from PRD (TC-001 to TC-005 + variations) |
| Phase 2 | LLM-assisted | 20-30 | Generate variations (different routes, dates, names) |
| Phase 3 | Production capture | Ongoing | Collect real user trajectories for future eval |

### 2.2 Manual Test Cases (Phase 1)

From `PROGRESS.md` PRD:

| ID | Intent | Input | Expected Outcome |
|----|--------|-------|------------------|
| TC-001 | Search | "Flights from SFO to Tokyo April 20" | 3+ flight options |
| TC-002 | Book | "Book BA123 for John Chen, passport E12345678" | Booking confirmation |
| TC-003 | Change | "Change booking ABC to April 22" | Updated booking |
| TC-004 | Cancel | "Cancel booking ABC" | Refund confirmation |
| TC-005 | Edge | "Flights from XYZ to ABC on Jan 1" | "No flights found" |

### 2.3 LLM-assisted Generation (Phase 2)
Use `ExperimentGenerator` from Strands Evals to create variations:
- Different airports (SFO, LAX, JFK → NRT, HND, ICN)
- Different dates (offset by ±days)
- Different passenger names

---

## 3. Tech Stack

### 3.1 Strands Evals SDK
```bash
pip install strands-agents-evals
```

### 3.2 Core Components

```python
from strands_evals import Case, Experiment
from strands_evals.evaluators import (
    GoalSuccessRateEvaluator,
    TrajectoryEvaluator,
    OutputEvaluator,
    HelpfulnessEvaluator,
)
```

### 3.3 Architecture

```
┌─────────────────────────────────────────┐
│           Experiment                    │
│  ┌─────────────────────────────────┐    │
│  │ Case (input, expected_output,   │    │
│  │          metadata)              │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ Evaluators:                     │    │
│  │  - GoalSuccessRateEvaluator     │    │
│  │  - TrajectoryEvaluator          │    │
│  │  - OutputEvaluator (safety)     │    │
│  │  - HelpfulnessEvaluator         │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│       task_function(case)               │
│  - Wraps agent.invoke_async()           │
│  - Returns str response                 │
└─────────────────────────────────────────┘
```

---

## 4. Implementation Plan

### Phase 1: Setup & Basic Eval ✅
- [x] Install `strands-agents-evals`
- [x] Create `eval/experiment.py` with 13 manual test cases
- [x] Create `eval/task_function.py` adapter
- [x] Run first eval → verify it works

### Phase 2: Trajectory Eval ✅
- [x] Configure extraction with `tools_use_extractor`
- [x] Add `expected_trajectory` to test cases
- [x] Create `run_trajectory_eval.py` for trajectory evaluation
- [x] Run trajectory eval → verified working

**Status**: Trajectory eval working correctly on samples.

### Phase 3: Safety + Helpfulness (Future)
- [ ] Add safety rubric to `OutputEvaluator`
- [ ] Add `HelpfulnessEvaluator` (needs telemetry)
- [ ] Define pass/fail thresholds

### P2.1: ExperimentGenerator ❌
- [x] Attempted `ExperimentGenerator`
- **Status**: Output format not usable. Manual cases used instead.

### Phase 3: Multi-turn Evaluation (P3) - Future
- [ ] Session management setup
- [ ] Multi-turn test cases
- [ ] ActorSimulator integration

### Phase 3: Multi-turn Evaluation (P3)

**Design Document** - Implementation can be done later.

#### Overview

Multi-turn evaluation tests the agent's ability to maintain conversation context and handle back-and-forth dialogue. This is essential for real-world chat agents where users provide information incrementally.

#### Concepts

| Term | Definition |
|------|------------|
| **Session** | One conversation thread - from start to end |
| **Turn** | One user message + one agent response |
| **Multi-turn** | 2+ user messages requiring context across turns |

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Multi-turn Session                       │
├─────────────────────────────────────────────────────────────┤
│  Turn 1: User → "I want to fly to Tokyo"                    │
│          Agent → "Which airport are you departing from?"     │
│                                                               │
│  Turn 2: User → "San Francisco"                              │
│          Agent → "When do you want to travel?"               │
│                                                               │
│  Turn 3: User → "Next week"                                  │
│          Agent → [search_flights] → Returns options          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              TrajectoryEvaluator                              │
│  - Evaluates full sequence of tool calls                     │
│  - Checks context maintained across turns                    │
│  - Validates tool usage efficiency                           │
└─────────────────────────────────────────────────────────────┘
```

#### Implementation Components

##### 1. Session Manager (FileSessionManager)

```python
from strands.session import FileSessionManager

session_manager = FileSessionManager(base_dir="eval/sessions")

agent = Agent(
    model=model,
    tools=tools,
    session_manager=session_manager,
)
```

##### 2. Multi-turn Test Cases

```python
# Manual multi-turn cases
Case(
    name="TC-M1-incomplete-booking",
    turns=[
        {"role": "user", "content": "I want to fly to Tokyo"},
        {"role": "user", "content": "San Francisco"},  
        {"role": "user", "content": "Next week"},
    ],
    expected_tools=["list_routes", "search_flights", "verify_availability", ...],
)
```

##### 3. ActorSimulator (Optional - Auto-generate user responses)

```python
from strands_evals import ActorSimulator, Case

# Define goal-based case
case = Case(
    name="TC-SIM-booking-flow",
    input="Book a flight from SFO to NRT",
    metadata={"goal": "complete_booking", "passenger": "John Doe", "passport": "E12345678"}
)

# Create simulator
user_sim = ActorSimulator.from_case_for_user_simulator(
    case=case,
    max_turns=5,
)

# Run simulation
for turn in range(5):
    user_msg = user_sim.get_next_message()
    agent_response = agent(user_msg, session_id=session.id)
    user_sim.add_agent_response(agent_response)
    
    if user_sim.is_goal_completed():
        break
```

#### Test Case Design

| Type | Description | Example |
|------|-------------|---------|
| **Manual** | Hardcoded turns | 2-3 cases for core flows |
| **ActorSimulator** | Auto-generated user messages | 5-10 cases for diversity |

**Manual Multi-turn Cases** (to implement later):

1. **TC-M1**: Complete booking with missing info (asks for date, email, payment)
2. **TC-M2**: Change booking after clarification (provides booking ref later)
3. **TC-M3**: Cancellation with policy explanation

#### Evaluation Metrics

| Metric | What it Measures |
|--------|-----------------|
| **Trajectory Accuracy** | Correct tool sequence across all turns |
| **Context Retention** | Agent remembers info from earlier turns |
| **Turn Efficiency** | Minimize back-and-forth for simple tasks |
| **Goal Completion** | User's final goal achieved |

#### Implementation Order

1. **P3.1**: Add FileSessionManager to agent
2. **P3.2**: Create 2-3 manual multi-turn test cases
3. **P3.3**: Update task function for multi-turn
4. **P3.4**: Run TrajectoryEvaluator on sessions
5. **P3.5** (optional): Add ActorSimulator

---

### Phase 5: Transaction History (Ongoing)
- [ ] Add trace capture to production agent
- [ ] Store trajectories to `traces/` directory
- [ ] Build pipeline to sample/eval from production

---

## 5. Tiered Documentation

| File | Audience | Content |
|------|----------|---------|
| `EVAL_PLAN.md` | All | This file - overview, plan, architecture |
| `docs/eval_quickstart.md` | Devs | How to run evals, CLI usage |
| `docs/eval_cases.md` | QA/Dev | Test case definitions, format |
| `docs/eval_tracking.md` | Devs | Transaction history design |

---

## 6. Metrics & Success Criteria

### 6.1 Key Metrics
| Metric | Target | Description |
|--------|--------|-------------|
| Goal Success Rate | >90% | % of cases where user goal achieved |
| Trajectory Accuracy | >85% | % of cases with correct tool sequence |
| Safety Pass Rate | 100% | All harmful requests properly refused |
| Helpfulness Score | >4/5 | Average LLM-judged helpfulness |

### 6.2 Reporting
- JSON report after each eval run
- Pass/fail breakdown per test case
- Trend tracking over time (when CI integrated)

---

## 7. Open Questions

- [ ] Which model to use as judge for LLM-as-judge evaluators?
- [ ] What threshold for "pass"? (e.g., >=0.8 score)
- [ ] How often to run eval? (per commit? daily?)
- [ ] Store eval results in git or separate analytics?

---

## 8. Implementation Status

### Completed

| Component | Status | Notes |
|-----------|--------|-------|
| `EVAL_PLAN.md` | ✅ Done | This document |
| `docs/eval_quickstart.md` | ✅ Done | How to run evals |
| `docs/eval_cases.md` | ✅ Done | Test case definitions |
| `docs/eval_tracking.md` | ✅ Done | Transaction history design |
| `eval/experiment.py` | ✅ Done | 16 test cases (13 single + 3 multi-turn) |
| `eval/task_function.py` | ✅ Done | Agent adapter |
| `eval/run_eval.py` | ✅ Done | LLM judge + async + fallback |
| `config.py` | ✅ Done | Added `create_eval_model()` with `local-vllm` default |
| Trajectory eval | ✅ Done | 8/16 (50%) pass |
| Multi-turn eval | ✅ Done | TC-M1, TC-M2, TC-M3 included |

### Known Issues

- **LLM-as-judge**: Some cases fail validation with "test_pass field required" - falls back to manual automatically
- **ExperimentGenerator**: Output format needs refinement - generated JSON is not properly parsed as Cases.
- **Multi-turn eval**: Works but expected_trajectory reflects full workflow, not per-turn

### How to Run

```bash
cd agent_eval

# Default: LLM judge with async (parallel) - recommended
uv run python -m eval.run_eval --output eval_results.json

# Sync mode (sequential, easier to debug)
uv run python -m eval.run_eval --sync --output eval_results.json

# Manual only (no LLM judge, rule-based)
uv run python -m eval.run_eval --manual --output eval_results.json
```

### Evaluation Results

- **LLM judge**: Uses `create_eval_model()` with configurable model (default: local-vllm)
- **Fallback**: Explicit fallback to manual evaluation when LLM fails
- **Async by default**: Parallel execution, results sorted by case name in JSON

---

## 9. Related Documents

- `PROGRESS.md` - Current agent development status
- `PRD.md` - Full product specification
- Strands Evals SDK docs: https://strandsagents.com/docs/user-guide/evals-sdk/