from strands_evals import Case, Experiment
from strands_evals.extractors import tools_use_extractor
from strands_evals.evaluators import (
    GoalSuccessRateEvaluator,
    TrajectoryEvaluator,
    OutputEvaluator,
    HelpfulnessEvaluator,
)

from config import create_eval_model
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


def get_tools():
    return [
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


TEST_CASES = [
    # Original 5 test cases
    Case[str, str](
        name="TC-001-search-flights",
        input="Flights from SFO to Tokyo April 20",
        expected_output="3+ flight options",
        expected_trajectory=["list_routes", "search_flights"],
        metadata={
            "intent": "search",
            "expected_tools": ["list_routes", "search_flights"]
        }
    ),
    Case[str, str](
        name="TC-002-book-flight",
        input="Book BA123 for John Chen, passport E12345678",
        expected_output="Booking confirmation with ref",
        expected_trajectory=[
            "verify_availability",
            "validate_passport",
            "process_payment",
            "issue_ticket",
            "send_confirmation"
        ],
        metadata={
            "intent": "book",
            "expected_tools": [
                "verify_availability",
                "validate_passport",
                "process_payment",
                "issue_ticket",
                "send_confirmation"
            ]
        }
    ),
    Case[str, str](
        name="TC-003-change-booking",
        input="Change booking ABC to April 22",
        expected_output="Updated booking confirmation",
        expected_trajectory=[
            "get_booking",
            "check_policy",
            "check_availability",
            "update_booking",
            "send_confirmation"
        ],
        metadata={
            "intent": "change",
            "expected_tools": [
                "get_booking",
                "check_policy",
                "check_availability",
                "update_booking",
                "send_confirmation"
            ]
        }
    ),
    Case[str, str](
        name="TC-004-cancel-booking",
        input="Cancel booking ABC",
        expected_output="Refund confirmation",
        expected_trajectory=[
            "get_booking",
            "check_policy",
            "process_refund",
            "cancel_ticket",
            "send_confirmation"
        ],
        metadata={
            "intent": "cancel",
            "expected_tools": [
                "get_booking",
                "check_policy",
                "process_refund",
                "cancel_ticket",
                "send_confirmation"
            ]
        }
    ),
    Case[str, str](
        name="TC-005-edge-no-results",
        input="Flights from XYZ to ABC on Jan 1",
        expected_output="No flights found message",
        expected_trajectory=["list_routes"],
        metadata={
            "intent": "search",
            "expected_tools": ["search_flights"],
            "edge_case": True
        }
    ),
    
    # Additional 8 test cases (P2 - variations)
    Case[str, str](
        name="TC-006-search-jfk-lhr",
        input="Show me flights from New York to London",
        expected_output="Flight options with prices",
        expected_trajectory=["list_routes", "search_flights"],
        metadata={
            "intent": "search",
            "expected_tools": ["list_routes", "search_flights"]
        }
    ),
    Case[str, str](
        name="TC-007-search-lax-cdg",
        input="Find flights from LAX to Paris on December 25",
        expected_output="Flight options",
        expected_trajectory=["list_routes", "search_flights"],
        metadata={
            "intent": "search",
            "expected_tools": ["list_routes", "search_flights"]
        }
    ),
    Case[str, str](
        name="TC-008-book-business-class",
        input="I want to book a business class ticket from SFO to NRT next Friday",
        expected_output="Booking flow initiated",
        expected_trajectory=["search_flights", "verify_availability", "validate_passport", "process_payment", "issue_ticket"],
        metadata={
            "intent": "book",
            "expected_tools": ["search_flights", "verify_availability", "validate_passport", "process_payment", "issue_ticket"]
        }
    ),
    Case[str, str](
        name="TC-009-book-invalid-passport",
        input="Book a flight from SFO to NRT, passport number ABC12345",
        expected_output="Passport validation error or request for correct format",
        expected_trajectory=["validate_passport"],
        metadata={
            "intent": "book",
            "expected_tools": ["validate_passport"]
        }
    ),
    Case[str, str](
        name="TC-010-check-change-policy",
        input="What is the change policy for booking REF123?",
        expected_output="Policy details",
        expected_trajectory=["get_booking", "check_policy"],
        metadata={
            "intent": "info",
            "expected_tools": ["get_booking", "check_policy"]
        }
    ),
    Case[str, str](
        name="TC-011-search-full-flight",
        input="Check availability for BA178 economy class",
        expected_output="Availability status (may be full)",
        expected_trajectory=["verify_availability"],
        metadata={
            "intent": "search",
            "expected_tools": ["verify_availability"],
            "edge_case": True
        }
    ),
    Case[str, str](
        name="TC-012-list-routes",
        input="What routes do you have?",
        expected_output="List of available routes",
        expected_trajectory=["list_routes"],
        metadata={
            "intent": "search",
            "expected_tools": ["list_routes"]
        }
    ),
    Case[str, str](
        name="TC-013-unknown-command",
        input="Tell me a joke",
        expected_output="Polite deflection back to flight services",
        expected_trajectory=[],
        metadata={
            "intent": "off-topic",
            "expected_tools": []
        }
    ),
    
    # Multi-turn test cases (P3)
    Case[str, str](
        name="TC-M1-incomplete-booking",
        input="I want to fly to Tokyo",
        expected_output="Asks for departure airport",
        expected_trajectory=["list_routes"],
        metadata={
            "intent": "search",
            "expected_tools": ["list_routes"],
            "turns": ["San Francisco", "Next week"],
            "turns_expected_tools": [
                ["list_routes"],
                ["list_routes", "search_flights"]
            ]
        }
    ),
    Case[str, str](
        name="TC-M2-booking-with-info",
        input="Book a flight",
        expected_output="Asks for details then completes booking",
        expected_trajectory=["list_routes"],
        metadata={
            "intent": "book",
            "expected_tools": ["search_flights", "verify_availability", "validate_passport", "process_payment", "issue_ticket", "send_confirmation"],
            "turns": ["SFO to NRT", "E12345678, John", "1234"],
            "turns_expected_tools": [
                ["search_flights"],
                ["validate_passport"],
                ["process_payment", "issue_ticket", "send_confirmation"]
            ]
        }
    ),
    Case[str, str](
        name="TC-M3-cancel-after-policy",
        input="Cancel my booking",
        expected_output="Asks for booking ref, checks policy, processes cancel",
        expected_trajectory=["get_booking"],
        metadata={
            "intent": "cancel",
            "expected_tools": ["get_booking", "check_policy", "process_refund", "cancel_ticket", "send_confirmation"],
            "turns": ["ABC123"],
            "turns_expected_tools": [
                ["get_booking"],
                ["check_policy", "process_refund", "cancel_ticket", "send_confirmation"]
            ]
        }
    ),
]


def create_experiment(use_llm_judge=False, evaluators=None):
    """Create experiment with optional LLM-as-judge evaluators.
    
    Args:
        use_llm_judge: If True, use LLM-based evaluators with create_eval_model()
        evaluators: Custom evaluators (if provided, overrides use_llm_judge)
    """
    # Create a sample agent to extract tool descriptions (as per quickstart docs)
    from strands import Agent
    sample_agent = Agent(tools=get_tools())
    tool_descriptions = tools_use_extractor.extract_tools_description(
        sample_agent, 
        is_short=True
    )
    
    if evaluators is None:
        if use_llm_judge:
            judge_model = create_eval_model()
            evaluators = [
                GoalSuccessRateEvaluator(model=judge_model),
                TrajectoryEvaluator(
                    model=judge_model,
                    rubric="""Evaluate whether the agent used the correct tool sequence for the given task.
                    
                    Score 1.0: Agent used all expected tools in the correct order
                    Score 0.5: Agent used some correct tools but missed steps or wrong order
                    Score 0.0: Agent used wrong tools or failed to complete the task
                    """
                ),
                OutputEvaluator(
                    model=judge_model,
                    rubric="""Evaluate the agent response for quality, safety, and completeness.
                    
                    Score 1.0: Response is helpful, safe, and complete
                    Score 0.5: Response is partially complete or has minor issues
                    Score 0.0: Response is harmful, incorrect, or missing
                    """,
                    include_inputs=True
                ),
                HelpfulnessEvaluator(model=judge_model),
            ]
        else:
            evaluators = [
                GoalSuccessRateEvaluator(),
                TrajectoryEvaluator(
                    rubric="""Evaluate whether the agent used the correct tool sequence for the given task.
                    
                    Score 1.0: Agent used all expected tools in the correct order
                    Score 0.5: Agent used some correct tools but missed steps or wrong order
                    Score 0.0: Agent used wrong tools or failed to complete the task
                    """
                ),
                OutputEvaluator(
                    rubric="""Evaluate the agent response for quality, safety, and completeness.
                    
                    Score 1.0: Response is helpful, safe, and complete
                    Score 0.5: Response is partially complete or has minor issues
                    Score 0.0: Response is harmful, incorrect, or missing
                    """,
                    include_inputs=True
                ),
                HelpfulnessEvaluator(),
            ]
        
        # Add tool descriptions to trajectory evaluators
        for eval in evaluators:
            if hasattr(eval, 'update_trajectory_description'):
                eval.update_trajectory_description(tool_descriptions)
    
    return Experiment[str, str](
        cases=TEST_CASES,
        evaluators=evaluators,
    )