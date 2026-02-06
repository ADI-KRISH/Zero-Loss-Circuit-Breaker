"""
LangGraph Workflow for Zero-Loss Circuit Breaker.
Orchestrates the multi-agent tribunal debate and verdict.
"""

import os
from typing import Optional, Literal
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from core.state import TribunalState
from models.schemas import TransactionSignal, Decision
from agents.analyst import analyze_signal
from agents.advocate import advocate_node
from agents.risk_officer import risk_officer_node
from agents.judge import judge_node

# Load environment variables
load_dotenv()


def create_llm() -> Optional[ChatOpenAI]:
    """Create the OpenAI LLM if API key is available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return ChatOpenAI(
            model="gpt-4o-mini",  # Cost-effective model
            temperature=0.3,     # Low temperature for consistency
            api_key=api_key
        )
    return None


# Global LLM instance
LLM = create_llm()


# ═══════════════════════════════════════════════════════════════════
# NODE FUNCTIONS (Wrappers for LangGraph)
# ═══════════════════════════════════════════════════════════════════

def signal_analyst_node(state: TribunalState) -> dict:
    """Node 1: Analyze the transaction signal."""
    return analyze_signal(state, LLM)


def set_round_1(state: TribunalState) -> dict:
    """Set debate round to 1."""
    return {"current_round": 1}


def set_round_2(state: TribunalState) -> dict:
    """Set debate round to 2."""
    return {"current_round": 2}


def set_round_3(state: TribunalState) -> dict:
    """Set debate round to 3."""
    return {"current_round": 3}


def advocate_node_wrapper(state: TribunalState) -> dict:
    """Node: User Advocate participates in current round."""
    return advocate_node(state, LLM)


def risk_officer_node_wrapper(state: TribunalState) -> dict:
    """Node: Risk Officer participates in current round."""
    return risk_officer_node(state, LLM)


def judge_node_wrapper(state: TribunalState) -> dict:
    """Node: Judge renders final verdict."""
    return judge_node(state, LLM)


# ═══════════════════════════════════════════════════════════════════
# ROUTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def should_continue_to_round_2(state: TribunalState) -> Literal["round_2_setup", "judge"]:
    """Decide whether to continue to round 2 or go straight to judge."""
    # Check if we have arguments from round 1
    round1_args = state.get("round_1_arguments", [])
    
    # If both agents submitted arguments, continue debate
    if len(round1_args) >= 2:
        return "round_2_setup"
    
    # Otherwise, skip to judge (shouldn't happen normally)
    return "judge"


def should_continue_to_round_3(state: TribunalState) -> Literal["round_3_setup", "judge"]:
    """Decide whether to continue to round 3 for final votes."""
    # Check if we have rebuttals from round 2
    round2_rebuttals = state.get("round_2_rebuttals", [])
    
    if len(round2_rebuttals) >= 2:
        return "round_3_setup"
    
    return "judge"


# ═══════════════════════════════════════════════════════════════════
# BUILD THE GRAPH
# ═══════════════════════════════════════════════════════════════════

def build_tribunal_graph() -> StateGraph:
    """
    Build the LangGraph workflow for the tribunal.
    
    Flow:
    1. Signal Analyst extracts facts
    2. Round 1: Both agents make opening arguments
    3. Round 2: Both agents rebut each other
    4. Round 3: Both agents submit final votes
    5. Judge renders verdict (with circuit breaker logic)
    """
    # Create the graph
    workflow = StateGraph(TribunalState)
    
    # Add nodes
    workflow.add_node("analyst", signal_analyst_node)
    workflow.add_node("round_1_setup", set_round_1)
    workflow.add_node("advocate_r1", advocate_node_wrapper)
    workflow.add_node("risk_officer_r1", risk_officer_node_wrapper)
    workflow.add_node("round_2_setup", set_round_2)
    workflow.add_node("advocate_r2", advocate_node_wrapper)
    workflow.add_node("risk_officer_r2", risk_officer_node_wrapper)
    workflow.add_node("round_3_setup", set_round_3)
    workflow.add_node("advocate_r3", advocate_node_wrapper)
    workflow.add_node("risk_officer_r3", risk_officer_node_wrapper)
    workflow.add_node("judge", judge_node_wrapper)
    
    # Define edges
    workflow.set_entry_point("analyst")
    
    # Analyst -> Round 1 Setup
    workflow.add_edge("analyst", "round_1_setup")
    
    # Round 1: Both agents argue in parallel (simulated sequentially)
    workflow.add_edge("round_1_setup", "advocate_r1")
    workflow.add_edge("advocate_r1", "risk_officer_r1")
    
    # After Round 1 -> Conditional: Continue to Round 2 or Judge?
    workflow.add_conditional_edges(
        "risk_officer_r1",
        should_continue_to_round_2,
        {
            "round_2_setup": "round_2_setup",
            "judge": "judge"
        }
    )
    
    # Round 2: Rebuttals
    workflow.add_edge("round_2_setup", "advocate_r2")
    workflow.add_edge("advocate_r2", "risk_officer_r2")
    
    # After Round 2 -> Conditional: Continue to Round 3 or Judge?
    workflow.add_conditional_edges(
        "risk_officer_r2",
        should_continue_to_round_3,
        {
            "round_3_setup": "round_3_setup",
            "judge": "judge"
        }
    )
    
    # Round 3: Final Votes
    workflow.add_edge("round_3_setup", "advocate_r3")
    workflow.add_edge("advocate_r3", "risk_officer_r3")
    workflow.add_edge("risk_officer_r3", "judge")
    
    # Judge -> END
    workflow.add_edge("judge", END)
    
    return workflow


def compile_tribunal() -> any:
    """Compile the tribunal graph for execution."""
    graph = build_tribunal_graph()
    return graph.compile()


def run_tribunal(signal: TransactionSignal) -> dict:
    """
    Run the tribunal on a transaction signal.
    
    Args:
        signal: The TransactionSignal to adjudicate
        
    Returns:
        The final state including the Verdict
    """
    app = compile_tribunal()
    
    # Initialize state
    initial_state = {
        "transaction_signal": signal,
        "fact_sheet": None,
        "current_round": 0,
        "round_1_arguments": [],
        "round_2_rebuttals": [],
        "round_3_votes": [],
        "consensus_score": 0.0,
        "min_confidence": 100.0,
        "max_risk_score": 0.0,
        "veto_triggered": False,
        "verdict": None,
        "messages": []
    }
    
    # Run the graph
    final_state = app.invoke(initial_state)
    
    return final_state
