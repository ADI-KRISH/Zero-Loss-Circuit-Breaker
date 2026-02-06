"""
Risk Officer Agent - The financial security guardian.
Skeptical of all claims, prevents double-spend, can VETO risky actions.
"""

import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from models.schemas import (
    FactSheet,
    AgentArgument,
    AgentVote,
    Decision,
    BankStatus
)
from core.prompts import RISK_OFFICER_PROMPT, AGENT_NAMES
from core.state import CircuitBreakerThresholds


def build_round1_argument(fact_sheet: FactSheet, llm: Optional[ChatOpenAI] = None) -> AgentArgument:
    """
    Round 1: Opening Statement
    Risk Officer analyzes the FactSheet from a security perspective.
    """
    consistency = fact_sheet.data_consistency
    bank_status = fact_sheet.raw_signals.bank_status
    
    # THE 504 RULE - Non-negotiable
    if bank_status == BankStatus.TIMEOUT_504:
        position = Decision.DENY
        confidence = 95.0
        reasoning = """CRITICAL: Bank returned 504 GATEWAY TIMEOUT.
        This means the bank's state is UNKNOWN - the transaction may have succeeded or failed.
        If we refund now and the original transaction settles in 10 minutes, we will DOUBLE SPEND.
        This is a known fraud vector. I am invoking the 504 RULE: NO REFUND until bank state is confirmed."""
        evidence = [
            "Bank API: 504 GATEWAY TIMEOUT",
            "504 = Unknown state, NOT failed state",
            "Risk: Double-spend if original settles",
            "Historical data: 23% of 504s eventually succeed"
        ]
        return AgentArgument(
            agent_name=AGENT_NAMES["risk_officer"],
            position=position,
            reasoning=reasoning,
            evidence=evidence,
            confidence=confidence
        )
    
    # Pending transactions
    if bank_status == BankStatus.PENDING:
        position = Decision.DENY
        confidence = 90.0
        reasoning = "Transaction is still PENDING. Refunding a pending transaction guarantees double-spend if it completes."
        evidence = [
            "Bank API: PENDING",
            "Pending != Failed",
            "Must wait for final state"
        ]
        return AgentArgument(
            agent_name=AGENT_NAMES["risk_officer"],
            position=position,
            reasoning=reasoning,
            evidence=evidence,
            confidence=confidence
        )
    
    # Clear failure - can approve
    if consistency == "CONSISTENT" and not fact_sheet.ledger_entry_exists and bank_status == BankStatus.FAILED:
        position = Decision.REFUND
        confidence = 80.0
        reasoning = "Bank confirms failure, ledger confirms no entry. Safe to refund."
        evidence = [
            "Bank API: FAILED",
            "Ledger: No entry",
            "Data Consistency: CONSISTENT"
        ]
        return AgentArgument(
            agent_name=AGENT_NAMES["risk_officer"],
            position=position,
            reasoning=reasoning,
            evidence=evidence,
            confidence=confidence
        )
    
    # Clear success - deny refund
    if consistency == "CONSISTENT" and fact_sheet.ledger_entry_exists and bank_status == BankStatus.SUCCESS:
        position = Decision.DENY
        confidence = 90.0
        reasoning = "Transaction confirmed successful. User claim is invalid or fraudulent."
        evidence = [
            "Bank API: SUCCESS",
            "Ledger: Entry FOUND",
            "User claim contradicts all data sources"
        ]
        return AgentArgument(
            agent_name=AGENT_NAMES["risk_officer"],
            position=position,
            reasoning=reasoning,
            evidence=evidence,
            confidence=confidence
        )
    
    # Conflicting data - suspicious
    if consistency == "CONFLICTING":
        position = Decision.UNCERTAIN
        confidence = 60.0
        reasoning = "Data sources conflict. This could indicate system error OR fraud. Need investigation."
        evidence = [
            f"Bank says: {fact_sheet.bank_api_response}",
            f"Ledger says: {fact_sheet.ledger_state}",
            "Conflicting data is a fraud indicator"
        ]
        return AgentArgument(
            agent_name=AGENT_NAMES["risk_officer"],
            position=position,
            reasoning=reasoning,
            evidence=evidence,
            confidence=confidence
        )
    
    # Default: uncertain
    return AgentArgument(
        agent_name=AGENT_NAMES["risk_officer"],
        position=Decision.UNCERTAIN,
        reasoning="Insufficient data to make a safe determination.",
        evidence=["Need more information"],
        confidence=40.0
    )


def build_round2_rebuttal(
    fact_sheet: FactSheet,
    advocate_argument: AgentArgument,
    llm: Optional[ChatOpenAI] = None
) -> AgentArgument:
    """
    Round 2: Challenge & Rebuttal
    Risk Officer challenges Advocate's assumptions.
    """
    bank_status = fact_sheet.raw_signals.bank_status
    
    # If Advocate is pushing REFUND on uncertain data
    if advocate_argument.position == Decision.REFUND and fact_sheet.data_consistency != "CONSISTENT":
        reasoning = f"""CHALLENGE to Advocate's argument:
        
        The Advocate claims: "{advocate_argument.reasoning[:100]}..."
        
        This is DANGEROUS because:
        1. Data consistency is {fact_sheet.data_consistency}, not CONSISTENT
        2. The Advocate's confidence of {advocate_argument.confidence}% is not justified by facts
        3. Question: "What if the bank settles in 10 minutes?" - The Advocate has no answer.
        
        Customer satisfaction is important, but NOT at the cost of financial loss."""
        
        position = Decision.DENY
        confidence = 85.0
        evidence = [
            f"Advocate confidence ({advocate_argument.confidence}%) exceeds data certainty",
            "Double-spend risk is real and quantifiable",
            "Better to delay than to lose money"
        ]
    elif advocate_argument.position == Decision.REFUND and bank_status == BankStatus.TIMEOUT_504:
        # Critical 504 case
        reasoning = """THE 504 RULE APPLIES.
        
        The Advocate wants to refund during a 504 timeout. This is exactly how double-spend fraud works:
        1. User initiates real transaction
        2. Bank times out (504)
        3. User claims "it failed!" 
        4. We refund
        5. Original transaction settles
        6. User has product AND money = We lose
        
        I am exercising VETO power."""
        
        position = Decision.DENY
        confidence = 95.0
        evidence = [
            "504 TIMEOUT = UNKNOWN state",
            "Veto power invoked",
            "Historical fraud pattern match"
        ]
    else:
        # Advocate agrees or is uncertain
        reasoning = f"The Advocate's position of {advocate_argument.position.value} at {advocate_argument.confidence}% is noted. My risk assessment remains."
        position = Decision.UNCERTAIN if fact_sheet.data_consistency != "CONSISTENT" else advocate_argument.position
        confidence = 70.0
        evidence = [f"Advocate confidence: {advocate_argument.confidence}%"]
    
    return AgentArgument(
        agent_name=AGENT_NAMES["risk_officer"],
        position=position,
        reasoning=reasoning,
        evidence=evidence,
        confidence=confidence
    )


def build_final_vote(
    fact_sheet: FactSheet,
    my_round2: AgentArgument,
    advocate_round2: AgentArgument,
    llm: Optional[ChatOpenAI] = None
) -> AgentVote:
    """
    Round 3: Final Vote
    Risk Officer submits final decision with possible VETO.
    """
    bank_status = fact_sheet.raw_signals.bank_status
    
    # VETO CONDITIONS
    should_veto = False
    
    # Condition 1: 504 Timeout - ALWAYS VETO
    if bank_status == BankStatus.TIMEOUT_504:
        should_veto = True
        reasoning = "VETO TRIGGERED: 504 GATEWAY TIMEOUT. Cannot approve ANY action until bank confirms state."
        vote = Decision.DENY
        confidence = 95.0
    
    # Condition 2: Pending - ALWAYS VETO
    elif bank_status == BankStatus.PENDING:
        should_veto = True
        reasoning = "VETO TRIGGERED: Transaction still PENDING. Action blocked until completion."
        vote = Decision.DENY
        confidence = 90.0
    
    # Condition 3: High confidence risk + Advocate pushing for risky action
    elif (my_round2.confidence > CircuitBreakerThresholds.VETO_CONFIDENCE_THRESHOLD and 
          my_round2.position == Decision.DENY and 
          advocate_round2.position == Decision.REFUND):
        should_veto = True
        reasoning = f"VETO TRIGGERED: Risk confidence {my_round2.confidence}% exceeds threshold. Advocate wants REFUND but risk too high."
        vote = Decision.DENY
        confidence = my_round2.confidence
    
    # No veto - normal vote
    else:
        vote = my_round2.position
        confidence = my_round2.confidence
        reasoning = my_round2.reasoning
    
    return AgentVote(
        agent_name=AGENT_NAMES["risk_officer"],
        vote=vote,
        confidence=confidence,
        final_reasoning=reasoning,
        veto_triggered=should_veto
    )


def risk_officer_node(state: dict, llm: Optional[ChatOpenAI] = None) -> dict:
    """
    LangGraph node for Risk Officer.
    Handles all three rounds of debate.
    """
    fact_sheet = state.get("fact_sheet")
    current_round = state.get("current_round", 1)
    
    if current_round == 1:
        argument = build_round1_argument(fact_sheet, llm)
        return {
            "round_1_arguments": [argument],
            "messages": [(AGENT_NAMES["risk_officer"], f"Round 1: Position={argument.position.value}, Confidence={argument.confidence}%")]
        }
    elif current_round == 2:
        # Get Advocate's round 1 argument
        advocate_args = [a for a in state.get("round_1_arguments", []) if a.agent_name == AGENT_NAMES["advocate"]]
        advocate_arg = advocate_args[0] if advocate_args else None
        
        if advocate_arg:
            rebuttal = build_round2_rebuttal(fact_sheet, advocate_arg, llm)
            return {
                "round_2_rebuttals": [rebuttal],
                "messages": [(AGENT_NAMES["risk_officer"], f"Round 2 Rebuttal: Challenging Advocate's {advocate_arg.position.value} stance")]
            }
    elif current_round == 3:
        # Build final vote
        my_round2 = [a for a in state.get("round_2_rebuttals", []) if a.agent_name == AGENT_NAMES["risk_officer"]]
        advocate_round2 = [a for a in state.get("round_2_rebuttals", []) if a.agent_name == AGENT_NAMES["advocate"]]
        
        my_r2 = my_round2[0] if my_round2 else build_round1_argument(fact_sheet)
        advocate_r2 = advocate_round2[0] if advocate_round2 else AgentArgument(
            agent_name=AGENT_NAMES["advocate"],
            position=Decision.UNCERTAIN,
            reasoning="No response",
            confidence=50.0
        )
        
        vote = build_final_vote(fact_sheet, my_r2, advocate_r2, llm)
        
        # Update veto status in state
        return {
            "round_3_votes": [vote],
            "veto_triggered": vote.veto_triggered,
            "messages": [(AGENT_NAMES["risk_officer"], f"Final Vote: {vote.vote.value} at {vote.confidence}% confidence. VETO={vote.veto_triggered}")]
        }
    
    return {}
