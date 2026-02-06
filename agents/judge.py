"""
Judge Agent - The final arbiter of the tribunal.
Makes the final decision based on debate, enforces circuit breaker rules.
"""

from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from models.schemas import (
    FactSheet,
    AgentVote,
    Verdict,
    Decision,
    BankStatus
)
from core.prompts import JUDGE_PROMPT, AGENT_NAMES
from core.state import (
    CircuitBreakerThresholds,
    calculate_consensus,
    TribunalState
)


def render_verdict(state: dict, llm: Optional[ChatOpenAI] = None) -> dict:
    """
    Judge node function for LangGraph.
    Analyzes the entire debate and renders final verdict.
    
    Applies Circuit Breaker Rules:
    1. If ANY agent confidence < 40% → ESCALATE
    2. If consensus < 60% → ESCALATE
    3. If Risk Officer triggers VETO → ESCALATE
    4. If transaction state is INDETERMINATE (504, PENDING) → ESCALATE
    """
    fact_sheet: FactSheet = state.get("fact_sheet")
    votes: List[AgentVote] = state.get("round_3_votes", [])
    round1_args = state.get("round_1_arguments", [])
    round2_rebuttals = state.get("round_2_rebuttals", [])
    
    if not fact_sheet or not votes:
        return {
            "verdict": Verdict(
                transaction_id=state.get("transaction_signal", {}).get("transaction_id", "UNKNOWN"),
                decision=Decision.ESCALATE,
                confidence=0.0,
                reasoning="Insufficient data to render verdict. Missing fact sheet or votes.",
                circuit_breaker_triggered=True,
                escalation_reason="System error - incomplete deliberation"
            )
        }
    
    # Calculate metrics
    confidence_scores = [v.confidence for v in votes]
    min_confidence = min(confidence_scores) if confidence_scores else 0.0
    max_confidence = max(confidence_scores) if confidence_scores else 0.0
    consensus_score = calculate_consensus(votes)
    veto_triggered = any(v.veto_triggered for v in votes)
    
    # Check for INDETERMINATE transaction state
    bank_status = fact_sheet.raw_signals.bank_status
    is_indeterminate = bank_status in [BankStatus.TIMEOUT_504, BankStatus.PENDING]
    
    # Build debate summary
    debate_summary = _build_debate_summary(round1_args, round2_rebuttals, votes)
    
    # ═══════════════════════════════════════════════════════════════════
    # CIRCUIT BREAKER LOGIC - THE WINNING EQUATION
    # ═══════════════════════════════════════════════════════════════════
    
    circuit_breaker_triggered = False
    escalation_reason = None
    
    # Rule 1: Low Confidence
    if min_confidence < CircuitBreakerThresholds.MIN_CONFIDENCE_THRESHOLD:
        circuit_breaker_triggered = True
        escalation_reason = f"LOW CONFIDENCE: Minimum agent confidence ({min_confidence:.1f}%) below threshold ({CircuitBreakerThresholds.MIN_CONFIDENCE_THRESHOLD}%)"
    
    # Rule 2: Weak Agreement
    elif consensus_score < CircuitBreakerThresholds.CONSENSUS_THRESHOLD:
        circuit_breaker_triggered = True
        escalation_reason = f"WEAK AGREEMENT: Consensus ({consensus_score:.1f}%) below threshold ({CircuitBreakerThresholds.CONSENSUS_THRESHOLD}%)"
    
    # Rule 3: Veto Triggered
    elif veto_triggered:
        circuit_breaker_triggered = True
        risk_vote = next((v for v in votes if v.agent_name == AGENT_NAMES["risk_officer"]), None)
        escalation_reason = f"VETO TRIGGERED: Risk Officer blocked action. Reason: {risk_vote.final_reasoning[:100] if risk_vote else 'Unknown'}"
    
    # Rule 4: Indeterminate State
    elif is_indeterminate:
        circuit_breaker_triggered = True
        escalation_reason = f"INDETERMINATE STATE: Bank returned {bank_status.value}. Cannot confirm transaction state."
    
    # ═══════════════════════════════════════════════════════════════════
    # RENDER VERDICT
    # ═══════════════════════════════════════════════════════════════════
    
    if circuit_breaker_triggered:
        verdict = Verdict(
            transaction_id=fact_sheet.transaction_id,
            decision=Decision.ESCALATE,
            confidence=100.0 - consensus_score,  # High confidence in uncertainty
            reasoning=f"CIRCUIT BREAKER ACTIVATED. Strategic Refusal engaged. {escalation_reason}",
            circuit_breaker_triggered=True,
            escalation_reason=escalation_reason,
            debate_summary=debate_summary
        )
    else:
        # Consensus reached - determine majority decision
        vote_counts = {}
        for v in votes:
            vote_counts[v.vote] = vote_counts.get(v.vote, 0) + 1
        
        majority_vote = max(vote_counts, key=vote_counts.get)
        
        # Calculate combined confidence
        majority_votes_list = [v for v in votes if v.vote == majority_vote]
        avg_confidence = sum(v.confidence for v in majority_votes_list) / len(majority_votes_list)
        
        verdict = Verdict(
            transaction_id=fact_sheet.transaction_id,
            decision=majority_vote,
            confidence=avg_confidence,
            reasoning=f"Consensus reached: {majority_vote.value}. Both agents agreed with average confidence {avg_confidence:.1f}%.",
            circuit_breaker_triggered=False,
            escalation_reason=None,
            debate_summary=debate_summary
        )
    
    # Update state metrics
    return {
        "verdict": verdict,
        "consensus_score": consensus_score,
        "min_confidence": min_confidence,
        "max_risk_score": 100 - min_confidence,  # Inverse of min confidence
        "messages": [(AGENT_NAMES["judge"], f"VERDICT: {verdict.decision.value} | Circuit Breaker: {verdict.circuit_breaker_triggered}")]
    }


def _build_debate_summary(round1_args, round2_rebuttals, votes) -> str:
    """Build a human-readable summary of the debate."""
    lines = ["=== TRIBUNAL DEBATE LOG ===", ""]
    
    # Round 1
    lines.append("--- ROUND 1: Opening Statements ---")
    for arg in round1_args:
        lines.append(f"  {arg.agent_name}: {arg.position.value} ({arg.confidence:.0f}% confidence)")
        lines.append(f"    Reasoning: {arg.reasoning[:150]}...")
    
    # Round 2
    lines.append("")
    lines.append("--- ROUND 2: Challenge & Rebuttal ---")
    for arg in round2_rebuttals:
        lines.append(f"  {arg.agent_name}: {arg.position.value} ({arg.confidence:.0f}% confidence)")
        lines.append(f"    Rebuttal: {arg.reasoning[:150]}...")
    
    # Round 3
    lines.append("")
    lines.append("--- ROUND 3: Final Votes ---")
    for vote in votes:
        veto_str = " [VETO]" if vote.veto_triggered else ""
        lines.append(f"  {vote.agent_name}: {vote.vote.value} ({vote.confidence:.0f}% confidence){veto_str}")
    
    return "\n".join(lines)


def judge_node(state: dict, llm: Optional[ChatOpenAI] = None) -> dict:
    """
    LangGraph node for Judge.
    This is the final node that renders the verdict.
    """
    return render_verdict(state, llm)
