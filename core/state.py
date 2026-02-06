"""
LangGraph State Definitions for Zero-Loss Circuit Breaker.
Defines the shared state that flows through the agent graph.
"""

from typing import Annotated, List, Optional, Tuple
from typing_extensions import TypedDict

from models.schemas import (
    TransactionSignal,
    FactSheet,
    AgentArgument,
    AgentVote,
    DebateLog,
    Verdict,
    Decision
)


def merge_arguments(existing: List[AgentArgument], new: List[AgentArgument]) -> List[AgentArgument]:
    """Reducer to merge argument lists."""
    return existing + new


def merge_votes(existing: List[AgentVote], new: List[AgentVote]) -> List[AgentVote]:
    """Reducer to merge vote lists."""
    return existing + new


def merge_messages(existing: List[Tuple[str, str]], new: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Reducer to merge debug message lists."""
    return existing + new


class TribunalState(TypedDict):
    """
    The shared state for the Zero-Loss Circuit Breaker tribunal.
    This state flows through all nodes in the LangGraph.
    """
    # Input
    transaction_signal: TransactionSignal
    
    # Signal Analyst Output
    fact_sheet: Optional[FactSheet]
    
    # Debate State
    current_round: int
    round_1_arguments: Annotated[List[AgentArgument], merge_arguments]
    round_2_rebuttals: Annotated[List[AgentArgument], merge_arguments]
    round_3_votes: Annotated[List[AgentVote], merge_votes]
    
    # Decision Metrics
    consensus_score: float  # 0-100, how much agents agree
    min_confidence: float   # Lowest confidence among agents
    max_risk_score: float   # Highest risk identified
    veto_triggered: bool
    
    # Final Output
    verdict: Optional[Verdict]
    
    # Debug/Logging (simple tuple list, not LangChain messages)
    messages: Annotated[List[Tuple[str, str]], merge_messages]



# Threshold constants for circuit breaker logic
class CircuitBreakerThresholds:
    """
    The mathematical conditions that trigger strategic refusal.
    These are the "Winning Equation" from the implementation plan.
    """
    MIN_CONFIDENCE_THRESHOLD = 40.0  # If any agent < 40%, REFUSE
    CONSENSUS_THRESHOLD = 60.0       # If consensus < 60%, REFUSE
    VETO_CONFIDENCE_THRESHOLD = 80.0 # If Risk Officer > 80% confident in risk, VETO
    INDETERMINATE_STATES = ["TIMEOUT_504", "PENDING"]  # Auto-trigger circuit breaker


def should_trigger_circuit_breaker(state: TribunalState) -> bool:
    """
    Determines if the circuit breaker should be triggered.
    Returns True if ANY of the refusal conditions are met.
    """
    thresholds = CircuitBreakerThresholds
    
    # Condition 1: Low Confidence
    if state.get("min_confidence", 100) < thresholds.MIN_CONFIDENCE_THRESHOLD:
        return True
    
    # Condition 2: Weak Agreement
    if state.get("consensus_score", 100) < thresholds.CONSENSUS_THRESHOLD:
        return True
    
    # Condition 3: Veto Triggered
    if state.get("veto_triggered", False):
        return True
    
    # Condition 4: Indeterminate Transaction State
    signal = state.get("transaction_signal")
    if signal and signal.bank_status.value in thresholds.INDETERMINATE_STATES:
        return True
    
    return False


def calculate_consensus(votes: List[AgentVote]) -> float:
    """
    Calculate the consensus score from agent votes.
    Returns a percentage of how much the agents agree.
    """
    if not votes:
        return 0.0
    
    # Count votes by decision
    vote_counts = {}
    for vote in votes:
        decision = vote.vote.value
        vote_counts[decision] = vote_counts.get(decision, 0) + 1
    
    # Consensus is the percentage of the majority vote
    max_votes = max(vote_counts.values())
    consensus = (max_votes / len(votes)) * 100
    
    return consensus
