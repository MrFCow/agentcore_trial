import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from strands import Agent
from strands.session import FileSessionManager

from config import create_model
from eval.experiment import get_tools
from strands_evals.extractors import tools_use_extractor
from strands_evals.telemetry import StrandsEvalsTelemetry
from strands_evals.mappers import StrandsInMemorySessionMapper


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


# Telemetry for trace-based eval
_telemetry = None


def get_telemetry():
    """Initialize and return telemetry for trace-based evaluation."""
    global _telemetry
    if _telemetry is None:
        _telemetry = StrandsEvalsTelemetry()
        _telemetry.setup_in_memory_exporter()
    return _telemetry


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        model = create_model()
        _agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=get_tools(),
            callback_handler=None,
        )
    return _agent


def get_agent_with_session(session_id: str):
    """Agent with session manager for multi-turn eval.
    
    Args:
        session_id: Session ID to use/get
    
    Returns:
        tuple of (Agent, session_id)
    """
    model = create_model()
    session_manager = FileSessionManager(
        session_id=session_id,
        storage_dir="eval/sessions"
    )
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=get_tools(),
        session_manager=session_manager,
        callback_handler=None,
    )
    return agent, session_id


def get_response(case) -> str:
    """Task function for Strands Evals (simple version - returns just string).
    
    Takes a Case and returns the agent's response as a string.
    """
    agent = get_agent()
    result = agent(case.input)
    
    if isinstance(result, dict):
        if 'message' in result and isinstance(result['message'], dict):
            content = result['message'].get('content', '')
            if isinstance(content, list):
                return ' '.join(c.get('text', str(c)) for c in content)
            return str(content)
        return str(result)
    
    if hasattr(result, 'message'):
        msg = result.message
        if isinstance(msg, dict):
            content = msg.get('content', '')
            if isinstance(content, list):
                return ' '.join(c.get('text', str(c)) for c in content)
            return str(content)
        elif hasattr(msg, 'content'):
            return str(msg.content)
    return str(result)


def get_response_with_trajectory(case) -> Dict[str, Any]:
    """Task function that returns both output and trajectory.
    
    This is required for TrajectoryEvaluator and other trace-based evaluators.
    
    Returns:
        dict with keys:
            - output: str - the agent's text response
            - trajectory: list - extracted tool calls from agent.messages
    """
    agent = get_agent()
    result = agent(case.input)
    
    output = ""
    if isinstance(result, dict):
        if 'message' in result and isinstance(result['message'], dict):
            content = result['message'].get('content', '')
            if isinstance(content, list):
                output = ' '.join(c.get('text', str(c)) for c in content)
            else:
                output = str(content)
        else:
            output = str(result)
    elif hasattr(result, 'message'):
        msg = result.message
        if isinstance(msg, dict):
            content = msg.get('content', '')
            if isinstance(content, list):
                output = ' '.join(c.get('text', str(c)) for c in content)
            else:
                output = str(content)
        elif hasattr(msg, 'content'):
            output = str(msg.content)
    else:
        output = str(result)
    
    trajectory = []
    if hasattr(agent, 'messages'):
        try:
            trajectory = tools_use_extractor.extract_agent_tools_used_from_messages(agent.messages)
        except Exception as e:
            print(f"Warning: Could not extract trajectory: {e}")
    
    return {
        "output": output,
        "trajectory": trajectory,
    }


def get_response_multiturn(case) -> Dict[str, Any]:
    """Multi-turn task function with session management.
    
    Handles cases with multiple turns (conversation history).
    
    Case format for multi-turn:
        case.input: string (initial user message)
        case.turns: list of additional user messages (optional)
        or case.metadata.get("turns"): list of turns
    
    Returns:
        dict with keys:
            - output: final agent response
            - trajectory: full session with all tool calls
            - session_id: session identifier
    """
    # Get session_id from case.metadata or generate new
    session_id = str(uuid.uuid4())
    if case.metadata and "session_id" in case.metadata:
        session_id = case.metadata["session_id"]
    
    # Clear previous traces
    telemetry = get_telemetry()
    telemetry.in_memory_exporter.clear()
    
    # Create agent with session manager
    model = create_model()
    session_manager = FileSessionManager(
        session_id=session_id,
        storage_dir="eval/sessions"
    )
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=get_tools(),
        session_manager=session_manager,
        trace_attributes={
            "gen_ai.conversation.id": session_id,
            "session.id": session_id,
        },
        callback_handler=None,
    )
    
    # First turn: initial input
    result = agent(case.input)
    all_outputs = [extract_output(result)]
    all_tool_calls = []
    
    # Extract tool calls from first turn
    if hasattr(agent, 'messages'):
        try:
            tool_calls = tools_use_extractor.extract_agent_tools_used_from_messages(agent.messages)
            all_tool_calls.extend(tool_calls)
        except Exception as e:
            print(f"Warning: Could not extract trajectory: {e}")
    
    # Additional turns (from metadata.turns or case.turns)
    turns = case.metadata.get("turns", []) if case.metadata else []
    
    for turn_input in turns:
        if isinstance(turn_input, dict):
            turn_message = turn_input.get("content", str(turn_input))
        else:
            turn_message = str(turn_input)
        
        # Continue conversation with session
        result = agent(turn_message, session_id=session_id)
        all_outputs.append(extract_output(result))
        
        # Extract tool calls
        if hasattr(agent, 'messages'):
            try:
                tool_calls = tools_use_extractor.extract_agent_tools_used_from_messages(agent.messages)
                all_tool_calls.extend(tool_calls)
            except Exception as e:
                print(f"Warning: Could not extract trajectory: {e}")
    
    # Map spans to session for trace-based evaluation
    finished_spans = telemetry.in_memory_exporter.get_finished_spans()
    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(finished_spans, session_id=session_id)
    
    return {
        "output": "\n\n".join(all_outputs),
        "trajectory": all_tool_calls,
        "session": session,
        "session_id": session_id,
    }


def extract_output(result) -> str:
    """Extract output text from agent result."""
    if isinstance(result, dict):
        if 'message' in result and isinstance(result['message'], dict):
            content = result['message'].get('content', '')
            if isinstance(content, list):
                return ' '.join(c.get('text', str(c)) for c in content)
            return str(content)
        return str(result)
    
    if hasattr(result, 'message'):
        msg = result.message
        if isinstance(msg, dict):
            content = msg.get('content', '')
            if isinstance(content, list):
                return ' '.join(c.get('text', str(c)) for c in content)
            return str(content)
        elif hasattr(msg, 'content'):
            return str(msg.content)
    return str(result)


async def get_response_async(case) -> str:
    """Async version of task function for Strands Evals."""
    agent = get_agent()
    result = await agent.invoke_async(case.input)
    
    if hasattr(result, 'message') and result.message:
        return str(result.message.content)
    return str(result)


async def get_response_with_trajectory_async(case) -> Dict[str, Any]:
    """Async version that returns both output and trajectory."""
    agent = get_agent()
    result = await agent.invoke_async(case.input)
    
    output = ""
    if hasattr(result, 'message') and result.message:
        output = str(result.message.content)
    else:
        output = str(result)
    
    trajectory = []
    if hasattr(agent, 'messages'):
        try:
            trajectory = tools_use_extractor.extract_agent_tools_used_from_messages(agent.messages)
        except Exception as e:
            print(f"Warning: Could not extract trajectory: {e}")
    
    return {
        "output": output,
        "trajectory": trajectory,
    }


def reset_agent():
    """Reset the agent to clear conversation history between eval runs."""
    global _agent, _agent_with_session
    _agent = None
    _agent_with_session = None