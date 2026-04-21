from datetime import datetime
from typing import List, Optional, Dict, Any
from strands import tool
from data import flight_store


def get_store() -> Any:
    return flight_store


@tool
def list_routes() -> List[Dict[str, str]]:
    """List all available flight routes.
    
    Returns:
        List of available routes with origin and destination airport codes.
    """
    routes = []
    for route in flight_store.routes.values():
        routes.append({
            "origin": route.origin,
            "destination": route.destination,
            "route_id": route.id,
        })
    return sorted(routes, key=lambda x: (x["origin"], x["destination"]))


@tool
def search_flights(
    origin: str,
    destination: str,
    date: Optional[str] = None,
    fare_class: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search for available flights between origin and destination.
    
    Args:
        origin: Origin airport code (e.g., SFO, JFK, LAX)
        destination: Destination airport code (e.g., NRT, LHR, CDG)
        date: Departure date in YYYY-MM-DD format (optional)
        fare_class: Fare class preference (ECONOMY, BUSINESS, FIRST) (optional)
    
    Returns:
        List of available flights with details
    """
    results = []
    
    # Find matching routes
    matching_routes = [
        r for r in flight_store.routes.values()
        if r.origin == origin.upper() and r.destination == destination.upper()
    ]
    
    if not matching_routes:
        return [{"error": f"No routes found from {origin} to {destination}"}]
    
    route = matching_routes[0]
    
    # Find matching flights for this route
    for flight in flight_store.flights.values():
        if flight.route_id != route.id:
            continue
            
        # Filter by date if provided
        if date:
            flight_date = flight.departure_time.strftime("%Y-%m-%d")
            if flight_date != date:
                continue
        
        # Get pricing for each class
        fares = {}
        for class_type, fare_class_obj in flight.fare_classes.items():
            if fare_class and fare_class.upper() != class_type:
                continue
            fares[class_type] = {
                "price": fare_class_obj.base_price,
                "seats_available": fare_class_obj.seats_available,
                "refundable": fare_class_obj.fare_rules.refundable,
                "change_fee": fare_class_obj.fare_rules.change_fee,
            }
        
        results.append({
            "flight_id": flight.id,
            "airline": flight.airline,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_time": flight.departure_time.strftime("%Y-%m-%d %H:%M"),
            "arrival_time": flight.arrival_time.strftime("%Y-%m-%d %H:%M"),
            "aircraft": flight.aircraft,
            "fares": fares,
        })
    
    if not results:
        return [{"error": f"No flights found for {origin} to {destination} on {date}"}]
    
    return results


@tool
def verify_availability(flight_id: str, fare_class: str) -> Dict[str, Any]:
    """Verify seat availability for a specific flight and class.
    
    Args:
        flight_id: The flight identifier (e.g., BA123)
        fare_class: The fare class (ECONOMY, BUSINESS, FIRST)
    
    Returns:
        Availability status and details
    """
    flight = flight_store.flights.get(flight_id.upper())
    
    if not flight:
        return {"available": False, "error": f"Flight {flight_id} not found"}
    
    fare = flight.fare_classes.get(fare_class.upper())
    
    if not fare:
        return {"available": False, "error": f"Fare class {fare_class} not available"}
    
    if fare.seats_available <= 0:
        return {"available": False, "error": f"No seats available in {fare_class}"}
    
    return {
        "available": True,
        "flight_id": flight_id.upper(),
        "fare_class": fare_class.upper(),
        "seats_remaining": fare.seats_available,
        "price": fare.base_price
    }


@tool
def validate_passport(passport_number: str) -> Dict[str, Any]:
    """Validate passport number format.
    
    Args:
        passport_number: Passport number to validate
    
    Returns:
        Validation result
    """
    if not passport_number or len(passport_number) < 6:
        return {"valid": False, "error": "Passport number too short"}
    
    # Simple format check - alphanumeric, 6-9 characters
    if not passport_number.isalnum():
        return {"valid": False, "error": "Passport must be alphanumeric"}
    
    # Check if passport exists in our system
    for passenger in flight_store.passengers.values():
        if passenger.passport_number.upper() == passport_number.upper():
            return {
                "valid": True,
                "passport": passport_number.upper(),
                "registered": True,
                "name": passenger.name
            }
    
    return {
        "valid": True,
        "passport": passport_number.upper(),
        "registered": False
    }


@tool
def process_payment(
    card_last_four: str,
    amount: float,
    currency: str = "USD"
) -> Dict[str, Any]:
    """Process payment for a booking (mock implementation).
    
    Args:
        card_last_four: Last 4 digits of payment card
        amount: Amount to charge
        currency: Currency code (default USD)
    
    Returns:
        Payment result
    """
    # Mock payment - accept any 4-digit card
    if not card_last_four or len(card_last_four) != 4 or not card_last_four.isdigit():
        return {
            "success": False,
            "error": "Invalid card number - must be 4 digits"
        }
    
    # Mock: always succeed for valid cards
    return {
        "success": True,
        "transaction_id": f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "amount": amount,
        "currency": currency,
        "card_last_four": card_last_four,
        "timestamp": datetime.now().isoformat()
    }


@tool
def issue_ticket(
    passenger_name: str,
    passenger_passport: str,
    passenger_email: str,
    flight_id: str,
    fare_class: str,
    price_paid: float
) -> Dict[str, Any]:
    """Issue a flight ticket and create a booking.
    
    Args:
        passenger_name: Full name of passenger
        passenger_passport: Passport number
        passenger_email: Email address
        flight_id: Flight to book
        fare_class: Fare class (ECONOMY, BUSINESS, FIRST)
        price_paid: Amount paid
    
    Returns:
        Booking confirmation with ticket details
    """
    # Verify flight exists
    flight = flight_store.flights.get(flight_id.upper())
    if not flight:
        return {"success": False, "error": f"Flight {flight_id} not found"}
    
    # Verify availability
    fare = flight.fare_classes.get(fare_class.upper())
    if not fare or fare.seats_available <= 0:
        return {"success": False, "error": f"No availability in {fare_class}"}
    
    # Generate booking reference
    import uuid
    booking_ref = f"{flight.airline[:2]}{str(uuid.uuid4())[:6].upper()}"
    
# Find or create passenger
    passenger_id = None
    for p in flight_store.passengers.values():
        if p.passport_number.upper() == passenger_passport.upper():
            passenger_id = p.id
            break
    
    if not passenger_id:
        from data.store import Passenger
        passenger_id = f"p{len(flight_store.passengers) + 1}"
        new_passenger = Passenger(
            id=passenger_id,
            name=passenger_name,
            passport_number=passenger_passport.upper(),
            email=passenger_email,
            phone="+1-555-0000"
        )
        flight_store.passengers[passenger_id] = new_passenger
    
    # Create booking
    from data.store import Booking
    now = datetime.now()
    booking = Booking(
        id=booking_ref,
        passenger_id=passenger_id,
        passenger_name=passenger_name,
        passenger_passport=passenger_passport.upper(),
        passenger_email=passenger_email,
        flight_id=flight_id.upper(),
        fare_class=fare_class.upper(),
        status="CONFIRMED",
        total_paid=price_paid,
        created_at=now,
        updated_at=now
    )
    flight_store.bookings[booking_ref] = booking
    
    # Decrement seat availability
    fare.seats_available -= 1
    
    return {
        "success": True,
        "booking_reference": booking_ref,
        "ticket_number": f"{flight_id.upper()}{booking_ref[-6:]}",
        "passenger_name": passenger_name,
        "flight": {
            "flight_id": flight.id,
            "airline": flight.airline,
            "departure": flight.departure_time.strftime("%Y-%m-%d %H:%M"),
            "arrival": flight.arrival_time.strftime("%Y-%m-%d %H:%M"),
        },
        "fare_class": fare_class.upper(),
        "total_paid": price_paid
    }


@tool
def get_booking(booking_reference: str) -> Dict[str, Any]:
    """Retrieve booking details by reference.
    
    Args:
        booking_reference: The booking reference number
    
    Returns:
        Booking details
    """
    booking = flight_store.bookings.get(booking_reference.upper())
    
    if not booking:
        return {"error": f"Booking {booking_reference} not found"}
    
    # Get flight details
    flight = flight_store.flights.get(booking.flight_id)
    
    return {
        "booking_reference": booking.id,
        "passenger_name": booking.passenger_name,
        "passenger_passport": booking.passenger_passport,
        "passenger_email": booking.passenger_email,
        "status": booking.status,
        "total_paid": booking.total_paid,
        "created_at": booking.created_at.isoformat(),
        "flight": {
            "flight_id": flight.id if flight else "Unknown",
            "airline": flight.airline if flight else "Unknown",
            "departure": flight.departure_time.strftime("%Y-%m-%d %H:%M") if flight else "Unknown",
            "arrival": flight.arrival_time.strftime("%Y-%m-%d %H:%M") if flight else "Unknown",
            "fare_class": booking.fare_class
        } if flight else None
    }


@tool
def check_policy(booking_reference: str, action: str) -> Dict[str, Any]:
    """Check change/cancellation policy for a booking.
    
    Args:
        booking_reference: The booking reference number
        action: "change" or "cancel"
    
    Returns:
        Policy details including fees and refund eligibility
    """
    booking = flight_store.bookings.get(booking_reference.upper())
    
    if not booking:
        return {"error": f"Booking {booking_reference} not found"}
    
    if booking.status == "CANCELLED":
        return {"error": "Booking is already cancelled"}
    
    flight = flight_store.flights.get(booking.flight_id)
    if not flight:
        return {"error": "Flight details not found"}
    
    fare = flight.fare_classes.get(booking.fare_class)
    if not fare:
        return {"error": "Fare class not found"}
    
    rules = fare.fare_rules
    
    if action.lower() == "cancel":
        return {
            "action": "cancel",
            "refundable": rules.refundable,
            "cancel_fee": rules.cancel_fee,
            "refund_amount": booking.total_paid - rules.cancel_fee if rules.refundable else 0,
            "message": f"Cancellation fee: ${rules.cancel_fee}" if rules.cancel_fee > 0 else "Free cancellation"
        }
    
    elif action.lower() == "change":
        return {
            "action": "change",
            "change_fee": rules.change_fee,
            "message": f"Change fee: ${rules.change_fee}" if rules.change_fee > 0 else "Free changes"
        }
    
    return {"error": f"Unknown action: {action}"}


@tool
def check_availability(flight_id: str, fare_class: str) -> Dict[str, Any]:
    """Check availability for a specific flight (alias for verify_availability).
    
    Args:
        flight_id: The flight identifier
        fare_class: The fare class
    
    Returns:
        Availability status
    """
    return verify_availability(flight_id, fare_class)


@tool
def update_booking(
    booking_reference: str,
    new_flight_id: Optional[str] = None,
    new_fare_class: Optional[str] = None,
    change_fee: float = 0.0
) -> Dict[str, Any]:
    """Update/modify an existing booking.
    
    Args:
        booking_reference: The booking reference number
        new_flight_id: New flight ID (optional)
        new_fare_class: New fare class (optional)
        change_fee: Change fee to apply
    
    Returns:
        Updated booking details
    """
    booking = flight_store.bookings.get(booking_reference.upper())
    
    if not booking:
        return {"success": False, "error": f"Booking {booking_reference} not found"}
    
    if booking.status == "CANCELLED":
        return {"success": False, "error": "Cannot update a cancelled booking"}
    
    if new_flight_id:
        new_flight = flight_store.flights.get(new_flight_id.upper())
        if not new_flight:
            return {"success": False, "error": f"Flight {new_flight_id} not found"}
        booking.flight_id = new_flight_id.upper()
    
    if new_fare_class:
        new_fare = flight_store.flights.get(booking.flight_id).fare_classes.get(new_fare_class.upper())
        if not new_fare:
            return {"success": False, "error": f"Fare class {new_fare_class} not available"}
        booking.fare_class = new_fare_class.upper()
    
    booking.status = "CHANGED"
    booking.total_paid += change_fee
    booking.updated_at = datetime.now()
    
    return {
        "success": True,
        "booking_reference": booking.id,
        "changes": {
            "new_flight_id": new_flight_id.upper() if new_flight_id else None,
            "new_fare_class": new_fare_class.upper() if new_fare_class else None,
            "change_fee": change_fee
        },
        "total_paid": booking.total_paid,
        "status": booking.status
    }


@tool
def process_refund(booking_reference: str) -> Dict[str, Any]:
    """Process refund for a cancelled booking.
    
    Args:
        booking_reference: The booking reference number
    
    Returns:
        Refund details
    """
    booking = flight_store.bookings.get(booking_reference.upper())
    
    if not booking:
        return {"success": False, "error": f"Booking {booking_reference} not found"}
    
    flight = flight_store.flights.get(booking.flight_id)
    if flight:
        fare = flight.fare_classes.get(booking.fare_class)
        if fare:
            cancel_fee = fare.fare_rules.cancel_fee
            refund_amount = booking.total_paid - cancel_fee if fare.fare_rules.refundable else 0
    
    return {
        "success": True,
        "booking_reference": booking.id,
        "original_amount": booking.total_paid,
        "cancel_fee": cancel_fee if 'cancel_fee' in locals() else 0,
        "refund_amount": refund_amount if 'refund_amount' in locals() else booking.total_paid,
        "refund_to": f"Card ending in {booking.passenger_passport[-4:]}",
        "processing_time": "5-7 business days"
    }


@tool
def cancel_ticket(booking_reference: str) -> Dict[str, Any]:
    """Cancel/invalidate a ticket.
    
    Args:
        booking_reference: The booking reference number
    
    Returns:
        Cancellation result
    """
    booking = flight_store.bookings.get(booking_reference.upper())
    
    if not booking:
        return {"success": False, "error": f"Booking {booking_reference} not found"}
    
    if booking.status == "CANCELLED":
        return {"success": False, "error": "Booking is already cancelled"}
    
    booking.status = "CANCELLED"
    booking.updated_at = datetime.now()
    
    # Release seat back to availability
    flight = flight_store.flights.get(booking.flight_id)
    if flight:
        fare = flight.fare_classes.get(booking.fare_class)
        if fare:
            fare.seats_available += 1
    
    return {
        "success": True,
        "booking_reference": booking.id,
        "status": "CANCELLED",
        "cancelled_at": datetime.now().isoformat()
    }


@tool
def send_confirmation(recipient: str, content: str) -> Dict[str, Any]:
    """Send confirmation email/SMS (mock implementation).
    
    Args:
        recipient: Email or phone number
        content: Message content
    
    Returns:
        Send result
    """
    return {
        "success": True,
        "recipient": recipient,
        "message_type": "email" if "@" in recipient else "sms",
        "sent_at": datetime.now().isoformat(),
        "preview": content[:100] + "..." if len(content) > 100 else content
    }