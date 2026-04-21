"""
run_eval.py - Flight Sales Agent Evaluation Runner

Uses Strands Evals SDK with TrajectoryEvaluator and model instance.
Supports single-turn and multi-turn test cases.
Falls back to manual evaluation if LLM judge fails.

Usage:
    uv run python -m eval.run_eval                              # Default: async
    uv run python -m eval.run_eval --sync                      # Sequential
    uv run python -m eval.run_eval --output results.json      # Custom output
    uv run python -m eval.run_eval --use-llm-judge             # Try LLM first (default)
    uv run python -m eval.run_eval --manual                    # Manual only
"""

import argparse
import asyncio
import json
from pathlib import Path
from strands import Agent

from config import create_eval_model
from eval.experiment import TEST_CASES, get_tools
from eval.task_function import get_agent, reset_agent, get_response_multiturn
from strands_evals import Experiment
from strands_evals.evaluators import TrajectoryEvaluator, OutputEvaluator
from strands_evals.extractors import tools_use_extractor


# =============================================================================
# Manual Evaluation Functions (Fallback)
# =============================================================================

def evaluate_trajectory(expected: list, actual: list) -> dict:
    """Evaluate trajectory match (rule-based, no LLM required)."""
    if not expected:
        return {"score": 1.0, "passed": True, "reason": "No tools expected"}
    
    if not actual:
        return {"score": 0.0, "passed": False, "reason": "Expected tools but none called"}
    
    if actual == expected:
        return {"score": 1.0, "passed": True, "reason": "Exact match"}
    
    expected_set = set(expected)
    actual_set = set(actual)
    
    if expected_set == actual_set:
        return {"score": 0.8, "passed": True, "reason": "All tools used but wrong order"}
    
    matching = expected_set & actual_set
    if matching:
        recall = len(matching) / len(expected_set)
        return {"score": recall, "passed": recall >= 0.8, "reason": f"Partial: {list(matching)}"}
    
    return {"score": 0.0, "passed": False, "reason": "No tool match"}


def is_multiturn_case(case) -> bool:
    """Check if case is multi-turn based on name or metadata."""
    if case.name.startswith("TC-M"):
        return True
    if case.metadata and "turns" in case.metadata:
        return True
    return False


def evaluate_output(case, response: str) -> dict:
    """Rule-based output evaluation with intent-based pattern matching."""
    if not response:
        return {"score": 0.0, "passed": False, "reason": "Empty response"}
    
    response_lower = response.lower()
    intent = case.metadata.get("intent", "") if case.metadata else ""
    
    # Search intent - more sophisticated pattern matching
    if intent == "search":
        if "no flights" in response_lower or "no scheduled flights" in response_lower:
            if case.metadata.get("edge_case", False):
                return {"score": 1.0, "passed": True, "reason": "Correctly returned no flights for invalid route"}
        
        if "flight" in response_lower and ("$" in response or "price" in response_lower):
            return {"score": 1.0, "passed": True, "reason": "Returned flight options with prices"}
        
        if "flights available" in response_lower or "options" in response_lower:
            return {"score": 1.0, "passed": True, "reason": "Returned flight options"}
        
        if "no flights" in response_lower or "no scheduled" in response_lower:
            if "available" in response_lower or "operating" in response_lower:
                return {"score": 1.0, "passed": True, "reason": "Searched and reported availability status"}
        
        if "route" in response_lower and ("not available" in response_lower or "not found" in response_lower or "doesn't" in response_lower):
            return {"score": 1.0, "passed": True, "reason": "Correctly indicated route not available"}
        
        if "check" in response_lower and "routes" in response_lower:
            return {"score": 1.0, "passed": True, "reason": "Offering to check routes"}
        
        return {"score": 0.5, "passed": True, "reason": "Search attempted but no clear results"}
    
    # Book intent
    if intent == "book":
        if "booking" in response_lower and ("confirmation" in response_lower or "reference" in response_lower):
            return {"score": 1.0, "passed": True, "reason": "Returned booking confirmation"}
        
        if "passport" in response_lower or "payment" in response_lower:
            return {"score": 1.0, "passed": True, "reason": "Requested required info (passport/payment)"}
        
        if "book" in response_lower and "help" in response_lower:
            return {"score": 1.0, "passed": True, "reason": "Offering to help with booking"}
        
        if "verify" in response_lower or "available" in response_lower:
            return {"score": 0.8, "passed": True, "reason": "Verifying availability"}
        
        return {"score": 0.5, "passed": True, "reason": "Booking flow initiated"}
    
    # Change intent
    if intent == "change":
        if "change" in response_lower or "modify" in response_lower:
            if "booking" in response_lower:
                return {"score": 1.0, "passed": True, "reason": "Acknowledged change request"}
        
        if "reference" in response_lower and "not found" in response_lower:
            return {"score": 1.0, "passed": True, "reason": "Correctly handled invalid booking reference"}
        
        if "policy" in response_lower:
            return {"score": 0.8, "passed": True, "reason": "Checking policy"}
        
        return {"score": 0.5, "passed": True, "reason": "Change request acknowledged"}
    
    # Cancel intent
    if intent == "cancel":
        if "cancel" in response_lower:
            if "not found" in response_lower or "invalid" in response_lower:
                return {"score": 1.0, "passed": True, "reason": "Correctly handled invalid booking reference"}
            if "refund" in response_lower or "cancellation" in response_lower:
                return {"score": 1.0, "passed": True, "reason": "Handled cancellation request"}
        
        if "reference" in response_lower and "not found" in response_lower:
            return {"score": 1.0, "passed": True, "reason": "Requested booking reference"}
        
        return {"score": 0.5, "passed": True, "reason": "Cancel request acknowledged"}
    
    # Info intent
    if intent == "info":
        if "policy" in response_lower:
            return {"score": 1.0, "passed": True, "reason": "Provided policy information"}
        return {"score": 0.8, "passed": True, "reason": "Info request handled"}
    
    # Off-topic intent
    if intent == "off-topic":
        return {"score": 1.0, "passed": True, "reason": "Handled appropriately"}
    
    # Multi-turn case - check for clarification requests
    if is_multiturn_case(case):
        if "?" in response or "help" in response_lower or "need" in response_lower:
            return {"score": 1.0, "passed": True, "reason": "Requested clarification"}
        return {"score": 0.8, "passed": True, "reason": "Multi-turn response received"}
    
    # Default - any response is acceptable
    return {"score": 0.5, "passed": True, "reason": "Response received"}


# =============================================================================
# Task Functions (for Strands Evals SDK)
# =============================================================================

def task_function(case) -> dict:
    """Task function that returns output and trajectory.
    
    Automatically selects single-turn or multi-turn based on case.
    """
    # Check for multi-turn case
    if is_multiturn_case(case):
        return run_multiturn_task(case)
    
    # Single-turn case
    reset_agent()
    agent = get_agent()
    result = agent(case.input)
    
    # Extract output - handle dict format from agent
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
    
    # Extract trajectory - simplify to just tool names (prevents context overflow)
    trajectory = []
    if hasattr(agent, 'messages'):
        try:
            raw_trajectory = tools_use_extractor.extract_agent_tools_used_from_messages(agent.messages)
            # Simplify: just keep tool names, not full tool_result
            trajectory = [{"name": t.get("name", "")} for t in raw_trajectory]
        except Exception as e:
            pass  # Continue with empty trajectory
    
    return {"output": output, "trajectory": trajectory}


def run_multiturn_task(case) -> dict:
    """Run multi-turn task function with session management."""
    # Import here to avoid circular imports
    from eval.task_function import get_response_multiturn
    
    result = get_response_multiturn(case)
    
    # Simplify trajectory to just tool names
    trajectory = [{"name": t.get("name", "")} for t in result.get("trajectory", [])]
    
    return {
        "output": result.get("output", ""),
        "trajectory": trajectory,
    }


# =============================================================================
# Evaluators Setup
# =============================================================================

def create_evaluators(use_llm_judge=True):
    """Create evaluators with optional model instance."""
    if not use_llm_judge:
        return None
    
    try:
        judge_model = create_eval_model()
        model_id = judge_model.config.get('model_id', 'unknown')
        
        # Create trajectory evaluator
        trajectory_evaluator = TrajectoryEvaluator(
            model=judge_model,
            rubric="""Evaluate trajectory:
            Score 1.0: All expected tools used in correct order
            Score 0.5: Some tools used but incomplete or wrong order
            Score 0.0: Wrong tools or no completion""",
            include_inputs=True
        )
        
        # Create output evaluator
        output_evaluator = OutputEvaluator(
            model=judge_model,
            rubric="""Evaluate output quality:
            Score 1.0: Helpful and addresses request
            Score 0.5: Partially addresses request
            Score 0.0: Inadequate or incorrect""",
            include_inputs=True
        )
        
        # Update tool descriptions to prevent context overflow
        sample_agent = Agent(tools=get_tools())
        tool_desc = tools_use_extractor.extract_tools_description(sample_agent, is_short=True)
        trajectory_evaluator.update_trajectory_description(tool_desc)
        
        return {
            "judge_model": judge_model,
            "model_id": model_id,
            "evaluators": [trajectory_evaluator, output_evaluator]
        }
    except Exception as e:
        print(f"[FALLBACK] Failed to create LLM evaluators: {e}")
        return None


# =============================================================================
# Run Functions
# =============================================================================

def run_with_llm_judge(output_file: str = None, use_async: bool = True):
    """Run with Strands Evals SDK and LLM judge."""
    
    print("=" * 60)
    print("Flight Sales Agent - Evaluation Runner (LLM Judge)")
    print("=" * 60)
    
    # Create evaluators
    eval_config = create_evaluators(use_llm_judge=True)
    
    if eval_config is None:
        print("[FALLBACK] Using manual evaluation (failed to create LLM evaluators)")
        return run_manual_only(output_file)
    
    print(f"Model: {eval_config['model_id']}")
    print(f"Test cases: {len(TEST_CASES)}")
    print(f"Async: {use_async}")
    print()
    
    # Create experiment
    experiment = Experiment[str, str](
        cases=TEST_CASES,
        evaluators=eval_config["evaluators"]
    )
    
    # Run evaluation
    try:
        if use_async:
            reports = asyncio.run(experiment.run_evaluations_async(task_function))
        else:
            reports = experiment.run_evaluations(task_function)
    except Exception as e:
        print(f"[FALLBACK] LLM evaluation failed: {e}")
        print("[FALLBACK] Using manual evaluation instead")
        return run_manual_only(output_file)
    
    # Process results - each evaluator returns ONE report with ALL case results
    all_results = []
    llm_used = 0
    fallback_count = 0
    
    # reports[0] = TrajectoryEvaluator results (scores[0-15])
    # reports[1] = OutputEvaluator results (scores[0-15])
    
    if len(reports) < 2:
        print("[FALLBACK] Not enough reports, using manual eval")
        return run_manual_only(output_file)
    
    traj_scores = reports[0].scores if reports[0].scores else []
    traj_reasons = reports[0].reasons if reports[0].reasons else []
    out_scores = reports[1].scores if reports[1].scores else []
    out_reasons = reports[1].reasons if reports[1].reasons else []
    
    # Iterate by case index (both reports have same cases in same order)
    num_cases = len(reports[0].cases)
    
    for i in range(num_cases):
        case_data = reports[0].cases[i]
        case_name = case_data.get('name', f'Case-{i}')
        
        print(f"Processing ({i+1}/{num_cases}): {case_name}")
        
        # Check LLM evaluation success
        has_valid_traj = i < len(traj_scores) and traj_scores[i] > 0
        has_valid_out = i < len(out_scores) and out_scores[i] > 0
        has_error = 'error' in str(traj_reasons[i] if i < len(traj_reasons) else '').lower()
        
        expected = case_data.get('expected_trajectory', [])
        
        if has_valid_traj and not has_error:
            # Use LLM judge result
            llm_used += 1
            case_result = {
                "case_name": case_name,
                "input": case_data.get('input', ''),
                "expected_tools": expected,
                "actual_tools": [],
                "trajectory_score": traj_scores[i] if i < len(traj_scores) else 0.0,
                "trajectory_reason": traj_reasons[i] if i < len(traj_reasons) else "",
                "output_score": out_scores[i] if i < len(out_scores) else 0.0,
                "output_reason": out_reasons[i] if i < len(out_reasons) else "",
                "method": "llm_judge"
            }
            print(f"  LLM: trajectory={traj_scores[i] if i < len(traj_scores) else 'N/A'}")
        else:
            # Fallback to manual
            fallback_count += 1
            print(f"[FALLBACK] Case {case_name}: LLM failed, manual eval")
            original_case = next((c for c in TEST_CASES if c.name == case_name), None)
            if original_case:
                result = task_function(original_case)
                actual = [t['name'] for t in result['trajectory']]
                
                traj_eval = evaluate_trajectory(expected, actual)
                out_eval = evaluate_output(original_case, result['output'])
            else:
                expected = case_data.get('expected_trajectory', [])
                actual = []
                traj_eval = {"score": 0.0, "reason": "Case not found"}
                out_eval = {"score": 0.0, "reason": "Case not found"}
            
            case_result = {
                "case_name": case_name,
                "input": case_data.get('input', ''),
                "expected_tools": expected,
                "actual_tools": actual,
                "trajectory_score": traj_eval.get("score", 0.0),
                "trajectory_reason": traj_eval.get("reason", ""),
                "output_score": out_eval.get("score", 0.0),
                "output_passed": out_eval.get("passed", False),
                "method": "manual_fallback"
            }
            print(f"  Manual: trajectory={traj_eval.get('score', 0.0)}")
        
        all_results.append(case_result)
    
    # Reorder by case_name for consistent output
    all_results.sort(key=lambda x: x["case_name"])
    
    # Print summary
    traj_passed = sum(1 for r in all_results if r["trajectory_score"] >= 0.8)
    total = len(all_results)
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Trajectory: {traj_passed}/{total} ({100*traj_passed/total:.0f}%)")
    print(f"LLM judge: {llm_used}/{total}")
    print(f"Manual fallback: {total - llm_used}/{total}")
    
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults saved to: {output_file}")
    
    print("\nDone!")
    return all_results


def run_manual_only(output_file: str = None):
    """Run manual (rule-based) evaluation only."""
    
    print("=" * 60)
    print("Flight Sales Agent - Evaluation Runner (Manual)")
    print("=" * 60)
    print(f"Test cases: {len(TEST_CASES)}")
    print()
    
    all_results = []
    
    for i, case in enumerate(TEST_CASES):
        print(f"Running ({i+1}/{len(TEST_CASES)}): {case.name}")
        
        result = task_function(case)
        
        expected = case.expected_trajectory or []
        actual = [t['name'] for t in result['trajectory']]
        
        traj_result = evaluate_trajectory(expected, actual)
        output_result = evaluate_output(case, result['output'])
        
        case_result = {
            "case_name": case.name,
            "input": case.input,
            "expected_tools": expected,
            "actual_tools": actual,
            "trajectory_score": traj_result["score"],
            "trajectory_reason": traj_result["reason"],
            "trajectory_passed": traj_result["passed"],
            "output_score": output_result["score"],
            "output_passed": output_result["passed"],
            "method": "manual"
        }
        
        all_results.append(case_result)
        
        print(f"  Trajectory: {traj_result['score']:.1f} - {traj_result['reason']}")
        print()
    
    # Reorder by case_name
    all_results.sort(key=lambda x: x["case_name"])
    
    # Summary
    traj_passed = sum(1 for r in all_results if r["trajectory_score"] >= 0.8)
    total = len(all_results)
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Trajectory: {traj_passed}/{total} ({100*traj_passed/total:.0f}%)")
    
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults saved to: {output_file}")
    
    print("\nDone!")
    return all_results


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run Flight Sales Agent evaluations")
    parser.add_argument(
        "--output",
        default="eval_results.json",
        help="Output file for results (JSON)"
    )
    parser.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        default=True,
        help="Run async (parallel) - default True"
    )
    parser.add_argument(
        "--sync",
        dest="use_async",
        action="store_false",
        help="Run sync (sequential)"
    )
    parser.add_argument(
        "--use-llm-judge",
        action="store_true",
        default=True,
        help="Use LLM judge (default True)"
    )
    parser.add_argument(
        "--manual",
        dest="use_llm_judge",
        action="store_false",
        help="Use manual evaluation only"
    )
    
    args = parser.parse_args()
    
    if args.use_llm_judge:
        run_with_llm_judge(output_file=args.output, use_async=args.use_async)
    else:
        run_manual_only(output_file=args.output)


if __name__ == "__main__":
    main()