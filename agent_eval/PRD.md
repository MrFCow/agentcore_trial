# PRD: Flight Sales Agent

## 1. Overview

**Product Name:** Flight Sales Agent  
**Type:** AI Agent / Conversational Assistant  
**Core Functionality:** A concierge-style agent that helps customers search flight availability, book flights, and manage booking changes/cancellations through natural conversation.  
**Target Users:** Individual travelers (B2C), travel agents (B2B)

---

## 2. Problem Statement

- Customers need 24/7 access to flight search and booking without waiting for human agents
- Manual flight booking is time-consuming - comparing across airlines, times, prices, classes
- Change/cancellation requires calling support or visiting website - high friction

---

## 3. Goals

- Enable customers to search, book, and manage flight bookings through natural conversation
- Reduce booking time from minutes to seconds
- Handle common operations (change/cancel) without human intervention

---

## 4. User Scenarios

| # | Scenario | User Input | Agent Action |
|---|----------|------------|--------------|
| 1 | Search Flights | "Flights from SFO to Tokyo on April 20?" | Parse request → Query availability → Return options with times, prices, airlines |
| 2 | Book Flight | "Book the BA123 flight for John Chen, passport E12345678" | Verify availability → Validate passport → Process payment → Issue ticket → Send confirmation |
| 3 | Change Flight | "Change booking ABC123 to April 22" | Get booking → Check change policy → Check new availability → Update booking → Confirm |
| 4 | Cancel Booking | "Cancel booking ABC123" | Get booking → Check cancellation policy → Process refund → Cancel ticket → Confirm |

---

## 5. Functional Requirements

### 5.1 Intent 1: Search Flights

**Input:** origin, destination, date, optional: return_date, class  
**Action:**
1. Parse user input for flight search parameters
2. Query flight database for matching routes
3. Return available options sorted by price or time

**Output:** List of available flights with:
- Airline name and flight number
- Departure and arrival times
- Price by class (Economy/Business/First)
- Seat availability

**Tools Used:** `search_flights`

### 5.2 Intent 2: Book Flight

**Input:** flight_id, passenger_name, passport_number, contact_email, payment_details  
**Action:**
1. Verify flight seat availability
2. Validate passport number format
3. Process payment
4. Issue ticket
5. Send confirmation email

**Output:** Booking confirmation with:
- Booking reference (e.g., "ABC123")
- Passenger name
- Flight details
- Ticket number
- Total amount paid

**Tools Used:** `verify_availability` → `validate_passport` → `process_payment` → `issue_ticket` → `send_confirmation`

### 5.3 Intent 3: Change/Cancel Booking

**Input:** booking_reference, action (change/cancel), optional: new_flight_id  
**Action:**
1. Retrieve existing booking
2. Check policy rules (change fee, refund eligibility)
3. If change: verify new flight availability → update booking
4. If cancel: calculate refund → cancel ticket
5. Send confirmation

**Output:**
- Change: Updated booking confirmation
- Cancel: Refund confirmation with amount

**Tools Used:** `get_booking` → `check_policy` → (`check_availability` + `update_booking`) OR (`process_refund` + `cancel_ticket`) → `send_confirmation`

---

## 6. Conversation Flow

```
User: "I need to fly from NYC to London on March 15"

Agent: Intent detected: SEARCH_FLIGHTS
Agent: "What class would you like? Economy, Business, or First?"

User: "Business please"

Agent: [calls search_flights(origin="JFK", destination="LHR", date="2024-03-15", class="BUSINESS")]
→ Returns 5 options

User: "Book the British Airways 10am one"

Agent: Intent detected: BOOK_FLIGHT
Agent: "I'll need passenger name, passport number, and payment information."

User: "John Chen, passport E12345678, card ending 4242"

Agent: [calls verify_availability → validate_passport → process_payment → issue_ticket → send_confirmation]
→ Returns: Booking confirmed! Reference: BA9X2Y, Ticket: 125-9876543
```

---

## 7. Data Schema

### 7.1 Route
```
Route {
  id: string (e.g., "route_sfo_nrt")
  origin: string (airport code: SFO, JFK, LHR, NRT)
  destination: string (airport code)
  distance_km: int
}
```

### 7.2 Flight
```
Flight {
  id: string (e.g., "BA123")
  route_id: string
  airline: string (e.g., "British Airways")
  departure_time: datetime
  arrival_time: datetime
  aircraft: string (e.g., "Boeing 777")
  fare_classes: {
    ECONOMY: FareClass
    BUSINESS: FareClass
    FIRST: FareClass
  }
}
```

### 7.3 FareClass
```
FareClass {
  class: string (ECONOMY | BUSINESS | FIRST)
  base_price: decimal
  seats_available: int
  fare_rules: FareRule
}
```

### 7.4 FareRule
```
FareRule {
  refundable: bool
  change_fee: decimal
  cancel_fee: decimal
  min_stay_days: int
  max_stay_days: int
}
```

### 7.5 Passenger
```
Passenger {
  id: string
  name: string
  passport_number: string
  email: string
  phone: string
}
```

### 7.6 Booking
```
Booking {
  id: string (booking reference)
  passenger_id: string
  flight_id: string
  fare_class: string
  status: enum (CONFIRMED, CHANGED, CANCELLED)
  total_paid: decimal
  created_at: datetime
  updated_at: datetime
}
```

---

## 8. Tools Specification

| # | Tool | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | list_routes | List available routes | - | List[Route] |
| 2 | search_flights | Query flight availability | origin, destination, date, class | List[FlightOption] |
| 3 | verify_availability | Confirm seat open | flight_id, seat_class | bool |
| 4 | validate_passport | Check passport format | passport_number | ValidationResult |
| 5 | process_payment | Charge payment method | payment_details | TransactionResult |
| 6 | issue_ticket | Generate ticket | passenger_info, flight | Ticket |
| 7 | get_booking | Retrieve booking | booking_ref | Booking |
| 8 | check_policy | Get change/cancel rules | booking_ref, action | PolicyResult |
| 9 | check_availability | Check new flight open | flight_id, class | bool |
| 10 | update_booking | Modify booking | booking_ref, changes | UpdatedBooking |
| 11 | process_refund | Calculate and process refund | booking_ref | RefundResult |
| 12 | cancel_ticket | Invalidate ticket | booking_ref | bool |
| 13 | send_confirmation | Email/SMS confirmation | recipient, content | bool |

---

## 9. Edge Cases

| # | Scenario | Expected Handling |
|---|----------|-------------------|
| 1 | No flights available | "No flights found for that route/date. Would you like different dates?" |
| 2 | Flight no longer available | "That flight just filled. Here are alternative options." |
| 3 | Invalid passport format | "Passport number appears invalid. Please verify and try again." |
| 4 | Payment declined | "Payment failed. Please try a different payment method." |
| 5 | Change fee applies | "Changing your flight costs $150. Proceed with the change?" |
| 6 | Non-refundable ticket | "This ticket is non-refundable. Would you like to change instead?" |
| 7 | Ambiguous search | "Did you mean [option A] or [option B]?" |
| 8 | Multi-passenger booking | Collect all passenger details before proceeding |

---

## 10. Evaluation Requirements

### 10.1 Evaluators

| Evaluator | What It Tests | Success Criteria |
|-----------|---------------|------------------|
| OutputEvaluator | Did agent return correct data? | Flight options match search; booking has correct details |
| TrajectoryEvaluator | Did agent follow correct tool sequence? | Book: verify → pay → issue → confirm; Change: get → policy → check → update |
| HelpfulnessEvaluator | Did user complete their goal? | User got what they wanted (flight booked, changed, cancelled) |

### 10.2 Test Cases (Required)

| ID | Intent | Input | Expected Tool Sequence | Expected Output |
|----|--------|-------|----------------------|-----------------|
| TC-001 | Search | "Flights from SFO to Tokyo April 20" | search_flights | 3+ options returned |
| TC-002 | Book | "Book BA123 for John Chen, passport E12345678" | verify → validate → pay → issue → confirm | Booking ref returned |
| TC-003 | Change | "Change booking ABC to April 22" | get_booking → check_policy → check_availability → update → confirm | Updated booking |
| TC-004 | Cancel | "Cancel booking ABC" | get_booking → check_policy → refund → cancel → confirm | Refund confirmation |
| TC-005 | Edge - No results | "Flights from XYZ to ABC on Jan 1" | search_flights | "No flights found" message |

---

## 11. Seed Data Requirements

### 11.1 Fleet Capacity (Private Jet Model)
| Class | Seats per Flight |
|-------|-----------------|
| ECONOMY | 20 |
| BUSINESS | 8 |
| FIRST | 4 |

### 11.2 Routes (Round-Trip Supported)
| Outbound | Return | Distance |
|----------|--------|----------|
| SFO → NRT | NRT → SFO | ~5,400 km |
| JFK → LHR | LHR → JFK | ~5,500 km |
| LAX → CDG | CDG → LAX | ~5,900 km |
| ORD → DXB | DXB → ORD | ~7,800 km |
| MIA → GRU | GRU → MIA | ~7,200 km |

Total: 10 routes (5 outbound + 5 return)

### 11.3 Flights Per Route
- 2-3 airlines per route
- 2-3 departure times per airline
- 3 fare classes per flight
- 30 days forward from reference date

### 11.4 Seed Bookings (Option B: Full Scenario Coverage)
| ID | Flight | Class | Status | Purpose |
|----|--------|-------|--------|---------|
| B1 | BA123 | BUSINESS | CONFIRMED | Standard booking |
| B2 | AA100 | ECONOMY | CONFIRMED | Standard booking |
| B3 | UA801 | BUSINESS | CONFIRMED | Standard booking |
| B4 | BA178 | FIRST | CANCELLED | Cancelled scenario |
| BOOKING5 | AF067 | FIRST | CHANGED | Changed scenario |
| B6 | BA178 | ECONOMY | CONFIRMED | Near departure (3 days) |
| B7 | VS004 | BUSINESS | CONFIRMED | Non-refundable fare |

### 11.5 Edge Cases
- 1 flight with ECONOMY fully booked (BA178, 0 seats available)
- Bookings decrement seat availability on creation
- Cancelled bookings release seats back to availability

---

## 12. Open Questions

| # | Question | Options |
|---|----------|---------|
| 1 | How to handle payment? | Mock for eval / Stripe integration / Other |
| 2 | Booking auto-confirm or ask confirmation? | Auto-confirm / Ask at key steps / Full confirmation |
| 3 | Multi-passenger support? | Yes / No (single passenger only) |
| 4 | Session memory? | Stateless / Remember within conversation / Persistent |
| 5 | Data storage? | In-memory dict / SQLite / JSON file |

---

## 13. Out of Scope (v1.0)

- Real payment processing
- Real airline API integration
- Multi-city itineraries
- Baggage/upgrade handling
- Loyalty program integration
- Refund to original payment method (mock only)