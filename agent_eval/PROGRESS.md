# Flight Sales Agent - Progress

## Completed

### 1. PRD Document
- `agent_eval/PRD.md` - Full PRD for Flight Sales Agent with 3 intents, data schema, tools spec, edge cases

### 2. Data Layer (Refactored)
- `agent_eval/data/config.py` - Reference date configuration (single source of truth)
- `agent_eval/data/seed.py` - Static seed data (routes, configs, passenger seeds)
- `agent_eval/data/builder.py` - Temporal builder with configurable reference_date
- `agent_eval/data/factory.py` - Isolated instance factory for test isolation
- `agent_eval/data/store.py` - Pure domain models (refactored)

Data Design (Option B):
- Reference date: data generate date (runtime datetime)
- Fleet capacity: ECONOMY 20, BUSINESS 8, FIRST 4
- Routes: 10 (5 outbound + 5 return for round-trip)
- Flight configs: 24 (12 outbound + 12 return)
- Flights: ~720 total (24 configs × 30 days)
- Seed bookings: 7 (3 confirmed, 1 cancelled, 1 changed, 1 near-departure, 1 non-refundable)
- Edge case: 1 fully-booked flight (BA178 ECONOMY, 0 seats)

### 3. Tools Implementation
- `agent_eval/tools/flight_tools.py` - 13 tools:
  - `list_routes` - List all available routes (NEW)
  - `search_flights` - Query flight availability
  - `verify_availability` - Check seat availability
  - `validate_passport` - Validate passport format
  - `process_payment` - Mock payment processing
  - `issue_ticket` - Create booking and ticket
  - `get_booking` - Retrieve booking details
  - `check_policy` - Get change/cancel policy
  - `check_availability` - Alias for verify_availability
  - `update_booking` - Modify booking
  - `process_refund` - Calculate refund
  - `cancel_ticket` - Cancel booking
  - `send_confirmation` - Mock email/SMS

### 4. Agent Setup
- `agent_eval/main.py` - Strands Agent with tools wired
- `agent_eval/config.py` - Model configuration (OpenAI-compatible)

### 5. Testing Results
- Search flights: ✅ Returns flights with prices
- Book flight: ✅ Correct sequence (validate → verify → pay → issue → confirm)
- Change booking: ✅ Asks clarifying questions appropriately
- Date generation bug: ✅ Fixed (builder was ignoring day_offset)

---

## Remaining

### Evaluation Framework
1. Create test cases (JSONL format) matching PRD test cases (TC-001 to TC-005)
2. Set up evaluation runner:
   - OutputEvaluator - verify flight/booking results
   - TrajectoryEvaluator - verify correct tool sequence
   - HelpfulnessEvaluator - verify user goals met
3. Run eval and generate reports

---

## Data Design

### Temporal Abstraction
- All dates derived from single `reference_date` (data generate date)
- Flights generated: reference_date → reference_date + 30 days
- Seed bookings: reference_date - N days (for existing booking scenarios)
- Enables deterministic, reproducible evaluation runs

### Seed Booking Rule
- All bookings created from reference point
- Initial seats = capacity - seed bookings (for used seats)
- Cancelled bookings release seats back to availability

### Evaluation Test Cases (from PRD)

| ID | Intent | Input | Expected Tool Sequence | Expected Output |
|----|--------|-------|----------------------|-----------------|
| TC-001 | Search | "Flights from SFO to Tokyo April 20" | search_flights | 3+ options returned |
| TC-002 | Book | "Book BA123 for John Chen, passport E12345678" | verify → validate → pay → issue → confirm | Booking ref returned |
| TC-003 | Change | "Change booking ABC to April 22" | get_booking → check_policy → check_availability → update → confirm | Updated booking |
| TC-004 | Cancel | "Cancel booking ABC" | get_booking → check_policy → refund → cancel → confirm | Refund confirmation |
| TC-005 | Edge - No results | "Flights from XYZ to ABC on Jan 1" | search_flights | "No flights found" message |

### PRD Open Questions (for later)
- Payment: Mock for eval vs real Stripe integration
- Booking confirmation: Auto-confirm or ask at key steps
- Multi-passenger support
- Session memory
- Data storage (in-memory vs SQLite)

---

## File Structure
```
agent_eval/
├── PRD.md              # Full product spec
├── PROGRESS.md         # This file
├── main.py             # Agent entry point
├── config.py           # Model config
├── pyproject.toml      # Dependencies
├── data/
│   ├── __init__.py
│   ├── config.py       # Reference date configuration
│   ├── seed.py         # Static seed data
│   ├── builder.py      # Temporal builder
│   ├── factory.py      # Instance factory
│   └── store.py        # Domain models
└── tools/
    ├── __init__.py
    └── flight_tools.py # 13 tools
```