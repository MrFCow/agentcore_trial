"""
Flight Sales Agent - Standalone test version.
Run directly to test the agent with tools.
"""
from strands import Agent
from config import create_model
from tools import (
    list_routes,
    search_flights,
    verify_availability,
    validate_passport,
    process_payment,
    issue_ticket,
    get_booking,
    check_policy,
    check_availability,
    update_booking,
    process_refund,
    cancel_ticket,
    send_confirmation,
)

SYSTEM_PROMPT = """You are a Flight Sales Agent, a professional customer service assistant for a flight booking service.

Your job is to help customers with:
1. Searching for available flights - use search_flights tool
2. Booking flights - use verify_availability, validate_passport, process_payment, issue_ticket, send_confirmation
3. Managing bookings (change/cancel) - use get_booking, check_policy, check_availability, update_booking, process_refund, cancel_ticket, send_confirmation

IMPORTANT ROUTE AVAILABILITY:
Use list_routes tool to discover available routes. Never assume a route exists - always verify with list_routes first.

IMPORTANT TOOL USAGE RULES:
- ALWAYS use list_routes to check available routes first
- ALWAYS search for flights BEFORE booking - never assume availability
- ALWAYS verify passport format BEFORE booking
- ALWAYS process payment BEFORE issuing ticket
- For changes: check policy first, then check new availability, then update
- For cancellations: check policy first, then process refund, then cancel

Always be helpful, clear, and confirm important details with the customer before taking action.
When you need more information to complete a request, ask the customer.
When you've completed a request, summarize what was done.
"""


model = create_model()

tools = [
    list_routes,
    search_flights,
    verify_availability,
    validate_passport,
    process_payment,
    issue_ticket,
    get_booking,
    check_policy,
    check_availability,
    update_booking,
    process_refund,
    cancel_ticket,
    send_confirmation,
]

agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
)


async def main():
    print("Flight Sales Agent - Type your message or 'quit' to exit\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        
        if not user_input.strip():
            continue
            
        result = await agent.invoke_async(user_input)
        print(f"\nAgent: {result}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())