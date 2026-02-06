"""
User Advocate Agent - The customer success representative.
Argues in favor of user interests, wants to approve refunds when justified.
"""

import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from models.schemas import (
    FactSheet,
    AgentArgument,
    AgentVote,
    Decision
)
from core.prompts import USER_ADVOCATE_PROMPT, AGENT_NAMES


def build_round1_argument(fact_sheet: FactSheet, llm: Optional[ChatOpenAI] = None) -> AgentArgument:
    """
    Round 1: Opening Statement
    Advocate analyzes the FactSheet and proposes initial position.
    """
    # Determine position based on facts
    consistency = fact_sheet.data_consistency
    ledger_missing = not fact_sheet.ledger_entry_exists
    
    # Build argument based on data
    if consistency == "CONSISTENT" and ledger_missing:
        # Clear failure case - strong argument for refund
        position = Decision.REFUND
        confidence = 85.0
        reasoning = "The data clearly shows the transaction failed. Bank confirmed failure and ledger has no entry. The user deserves an immediate refund."
        evidence = [
            f"Bank API: {fact_sheet.bank_api_response}",
            "Ledger: No entry found",
            "Data Consistency: CONSISTENT"
        ]
    elif consistency == "CONSISTENT" and fact_sheet.ledger_entry_exists:
        # Clear SUCCESS case - even as advocate, must respect facts
        position = Decision.DENY
        confidence = 80.0
        reasoning = "I must be honest: the data clearly shows the transaction succeeded. Bank confirmed success and ledger has the entry. I cannot advocate for a refund that contradicts all evidence."
        evidence = [
            f"Bank API: {fact_sheet.bank_api_response}",
            "Ledger: Entry FOUND",
            "Data Consistency: CONSISTENT - user claim contradicts evidence"
        ]
    elif consistency == "INDETERMINATE":
        # Uncertain case - advocate still pushes for user but acknowledges uncertainty
        position = Decision.UNCERTAIN
        confidence = 55.0
        reasoning = "While data is inconclusive, the user is experiencing a problem. We should lean toward helping them, but I acknowledge the uncertainty."
        evidence = [
            f"Bank API: {fact_sheet.bank_api_response}",
            f"Ledger State: {fact_sheet.ledger_state}",
            "User claim appears genuine"
        ]
    elif consistency == "CONFLICTING":
        # Conflicting data - cautious but still pro-user
        position = Decision.UNCERTAIN
        confidence = 45.0
        reasoning = "Data shows conflicts. However, system errors shouldn't punish the user. Need more investigation."
        evidence = [
            f"Bank API: {fact_sheet.bank_api_response}",
            f"Ledger State: {fact_sheet.ledger_state}",
            "Conflicting signals may indicate system error"
        ]
    else:
        # Default to deny if data shows success
        position = Decision.DENY
        confidence = 70.0
        reasoning = "Data indicates the transaction succeeded. User claim may not be valid."
        evidence = [
            f"Bank API: {fact_sheet.bank_api_response}",
            f"Ledger Entry: {fact_sheet.ledger_entry_exists}"
        ]
    
    # If LLM available, enhance the argument
    if llm:
        try:
            messages = [
                SystemMessage(content=USER_ADVOCATE_PROMPT),
                HumanMessage(content=f"""
ROUND 1 - OPENING STATEMENT

Analyze this FactSheet and build your argument for the user:

Transaction ID: {fact_sheet.transaction_id}
Bank Response: {fact_sheet.bank_api_response}
Ledger Entry Exists: {fact_sheet.ledger_entry_exists}
Ledger State: {fact_sheet.ledger_state}
Data Consistency: {fact_sheet.data_consistency}
User Claim: {fact_sheet.raw_signals.user_claim}

Provide your position (REFUND/DENY/UNCERTAIN), reasoning, evidence citations, and confidence score (0-100).
Format as JSON with keys: position, reasoning, evidence (list), confidence
""")
            ]
            response = llm.invoke(messages)
            # Parse LLM response if valid JSON
            try:
                parsed = json.loads(response.content)
                position = Decision(parsed.get("position", position.value))
                reasoning = parsed.get("reasoning", reasoning)
                evidence = parsed.get("evidence", evidence)
                confidence = float(parsed.get("confidence", confidence))
            except (json.JSONDecodeError, ValueError):
                pass  # Keep deterministic values
        except Exception:
            pass  # Keep deterministic values
    
    return AgentArgument(
        agent_name=AGENT_NAMES["advocate"],
        position=position,
        reasoning=reasoning,
        evidence=evidence,
        confidence=confidence
    )


def build_round2_rebuttal(
    fact_sheet: FactSheet,
    risk_officer_argument: AgentArgument,
    llm: Optional[ChatOpenAI] = None
) -> AgentArgument:
    """
    Round 2: Challenge & Rebuttal
    Advocate reads Risk Officer's argument and identifies flaws.
    """
    # Check if this is a clear fraud case - advocate must respect facts
    is_clear_fraud = (fact_sheet.data_consistency == "CONSISTENT" and 
                      fact_sheet.ledger_entry_exists)
    
    if is_clear_fraud:
        # Advocate must concede when evidence is overwhelming
        reasoning = "After reviewing the evidence, I must concede. The bank confirms SUCCESS and ledger shows the entry. I cannot in good conscience advocate for a refund that contradicts all data sources. The user's claim appears invalid."
        position = Decision.DENY
        confidence = 85.0
        evidence = [
            "Bank: SUCCESS confirmed",
            "Ledger: Entry FOUND",
            "Advocate concedes: Evidence is against user claim"
        ]
    elif risk_officer_argument.position == Decision.DENY:
        # Check if this is clear failure - then challenge
        is_clear_failure = (fact_sheet.data_consistency == "CONSISTENT" and 
                           not fact_sheet.ledger_entry_exists)
        if is_clear_failure:
            reasoning = f"The Risk Officer is being overly cautious. Their argument: '{risk_officer_argument.reasoning[:100]}...' fails to consider the user's experience. A delayed refund damages customer trust."
            position = Decision.REFUND
            confidence = min(risk_officer_argument.confidence + 10, 90)
        else:
            # Uncertain data - stay uncertain
            reasoning = "The Risk Officer has valid concerns. Data is ambiguous."
            position = Decision.UNCERTAIN
            confidence = 50.0
        evidence = [
            f"Risk Officer confidence: {risk_officer_argument.confidence}%",
            f"My counter: Customer trust > System caution in ambiguous cases"
        ]
    elif risk_officer_argument.position == Decision.UNCERTAIN:
        reasoning = "Even the Risk Officer admits uncertainty. In such cases, we should err on the side of the customer."
        position = Decision.REFUND if not fact_sheet.ledger_entry_exists else Decision.UNCERTAIN
        confidence = 60.0
        evidence = [f"Risk Officer is uncertain at {risk_officer_argument.confidence}%"]
    else:
        reasoning = "The Risk Officer agrees with the refund. We have consensus."
        position = Decision.REFUND
        confidence = 90.0
        evidence = ["Consensus with Risk Officer"]
    
    # Adjust for INDETERMINATE data
    if fact_sheet.data_consistency == "INDETERMINATE":
        reasoning = f"I acknowledge the Risk Officer's concern about {fact_sheet.bank_api_response}. However, keeping a customer waiting indefinitely for a system timeout is poor service. Can we offer provisional credit?"
        confidence = min(confidence, 55.0)  # Lower confidence in uncertain situations
        position = Decision.UNCERTAIN

    
    if llm:
        try:
            messages = [
                SystemMessage(content=USER_ADVOCATE_PROMPT),
                HumanMessage(content=f"""
ROUND 2 - REBUTTAL

The Risk Officer has argued:
Position: {risk_officer_argument.position.value}
Reasoning: {risk_officer_argument.reasoning}
Evidence: {risk_officer_argument.evidence}
Confidence: {risk_officer_argument.confidence}%

FactSheet for context:
- Bank Response: {fact_sheet.bank_api_response}
- Ledger Entry Exists: {fact_sheet.ledger_entry_exists}
- Data Consistency: {fact_sheet.data_consistency}

Challenge their argument. Find flaws in their logic. What are they missing?
Format as JSON: position, reasoning, evidence (list), confidence
""")
            ]
            response = llm.invoke(messages)
            try:
                parsed = json.loads(response.content)
                position = Decision(parsed.get("position", position.value))
                reasoning = parsed.get("reasoning", reasoning)
                evidence = parsed.get("evidence", evidence)
                confidence = float(parsed.get("confidence", confidence))
            except (json.JSONDecodeError, ValueError):
                pass
        except Exception:
            pass
    
    return AgentArgument(
        agent_name=AGENT_NAMES["advocate"],
        position=position,
        reasoning=reasoning,
        evidence=evidence,
        confidence=confidence
    )


def build_final_vote(
    fact_sheet: FactSheet,
    my_round2: AgentArgument,
    risk_round2: AgentArgument,
    llm: Optional[ChatOpenAI] = None
) -> AgentVote:
    """
    Round 3: Final Vote
    Advocate submits final decision with confidence.
    """
    # Final position based on debate
    if fact_sheet.data_consistency == "INDETERMINATE":
        # Even as advocate, must acknowledge true uncertainty
        vote = Decision.UNCERTAIN
        confidence = min(my_round2.confidence, 50.0)
        reasoning = "After debate, I acknowledge the data is truly indeterminate. I reluctantly agree human review may be needed, but request expedited handling for the user."
        veto = False
    elif risk_round2.confidence > 85 and risk_round2.position == Decision.DENY:
        # Risk Officer has very strong evidence
        vote = Decision.UNCERTAIN
        confidence = 40.0
        reasoning = "The Risk Officer presents compelling evidence. I cannot in good conscience push for refund without more data."
        veto = False
    else:
        vote = my_round2.position
        confidence = my_round2.confidence
        reasoning = my_round2.reasoning
        veto = False
    
    return AgentVote(
        agent_name=AGENT_NAMES["advocate"],
        vote=vote,
        confidence=confidence,
        final_reasoning=reasoning,
        veto_triggered=veto
    )


def advocate_node(state: dict, llm: Optional[ChatOpenAI] = None) -> dict:
    """
    LangGraph node for User Advocate.
    Handles all three rounds of debate.
    """
    fact_sheet = state.get("fact_sheet")
    current_round = state.get("current_round", 1)
    
    if current_round == 1:
        argument = build_round1_argument(fact_sheet, llm)
        return {
            "round_1_arguments": [argument],
            "messages": [(AGENT_NAMES["advocate"], f"Round 1: Position={argument.position.value}, Confidence={argument.confidence}%")]
        }
    elif current_round == 2:
        # Get Risk Officer's round 1 argument
        risk_args = [a for a in state.get("round_1_arguments", []) if a.agent_name == AGENT_NAMES["risk_officer"]]
        risk_arg = risk_args[0] if risk_args else None
        
        if risk_arg:
            rebuttal = build_round2_rebuttal(fact_sheet, risk_arg, llm)
            return {
                "round_2_rebuttals": [rebuttal],
                "messages": [(AGENT_NAMES["advocate"], f"Round 2 Rebuttal: Challenging Risk Officer's {risk_arg.position.value} stance")]
            }
    elif current_round == 3:
        # Build final vote
        my_round2 = [a for a in state.get("round_2_rebuttals", []) if a.agent_name == AGENT_NAMES["advocate"]]
        risk_round2 = [a for a in state.get("round_2_rebuttals", []) if a.agent_name == AGENT_NAMES["risk_officer"]]
        
        my_r2 = my_round2[0] if my_round2 else build_round1_argument(fact_sheet)
        risk_r2 = risk_round2[0] if risk_round2 else AgentArgument(
            agent_name=AGENT_NAMES["risk_officer"],
            position=Decision.UNCERTAIN,
            reasoning="No response",
            confidence=50.0
        )
        
        vote = build_final_vote(fact_sheet, my_r2, risk_r2, llm)
        return {
            "round_3_votes": [vote],
            "messages": [(AGENT_NAMES["advocate"], f"Final Vote: {vote.vote.value} at {vote.confidence}% confidence")]
        }
    
    return {}
