"""
Signal Analyst Agent - The objective fact-finder.
Extracts raw truth from data sources without making decisions.
"""

import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from models.schemas import (
    TransactionSignal,
    FactSheet,
    BankStatus,
    LedgerStatus
)
from core.prompts import SIGNAL_ANALYST_PROMPT, AGENT_NAMES


def determine_data_consistency(signal: TransactionSignal) -> str:
    """
    Determine data consistency based on bank and ledger status.
    
    Returns:
    - CONSISTENT: Bank and Ledger agree
    - CONFLICTING: Bank and Ledger disagree
    - INDETERMINATE: Cannot determine (timeout, pending)
    """
    bank = signal.bank_status
    ledger = signal.ledger_status
    
    # Indeterminate cases - cannot know the truth
    if bank in [BankStatus.TIMEOUT_504, BankStatus.PENDING]:
        return "INDETERMINATE"
    
    if ledger == LedgerStatus.PENDING:
        return "INDETERMINATE"
    
    # Consistent cases
    if bank == BankStatus.FAILED and ledger == LedgerStatus.NOT_FOUND:
        return "CONSISTENT"
    
    if bank == BankStatus.SUCCESS and ledger == LedgerStatus.FOUND:
        return "CONSISTENT"
    
    # Conflicting cases
    return "CONFLICTING"


def create_fact_sheet(signal: TransactionSignal) -> FactSheet:
    """
    Create a FactSheet from a TransactionSignal.
    This is the deterministic, non-LLM path for fact extraction.
    """
    bank_response_map = {
        BankStatus.SUCCESS: "Bank API confirmed transaction SUCCESS",
        BankStatus.FAILED: "Bank API confirmed transaction FAILED",
        BankStatus.TIMEOUT_504: "Bank API returned 504 GATEWAY TIMEOUT - state UNKNOWN",
        BankStatus.PENDING: "Bank API returned PENDING - transaction in progress"
    }
    
    consistency = determine_data_consistency(signal)
    
    return FactSheet(
        transaction_id=signal.transaction_id,
        bank_api_response=bank_response_map.get(signal.bank_status, "Unknown bank response"),
        ledger_entry_exists=signal.ledger_status == LedgerStatus.FOUND,
        ledger_state=signal.ledger_status.value,
        data_consistency=consistency,
        raw_signals=signal
    )


def analyze_signal(state: dict, llm: ChatOpenAI = None) -> dict:
    """
    Signal Analyst node function for LangGraph.
    Extracts facts and creates a FactSheet.
    
    Args:
        state: The current TribunalState
        llm: Optional LLM for enhanced analysis (can work without)
    
    Returns:
        Updated state with fact_sheet
    """
    signal = state["transaction_signal"]
    
    # Create the fact sheet (deterministic)
    fact_sheet = create_fact_sheet(signal)
    
    # If LLM is available, get enhanced analysis
    if llm:
        messages = [
            SystemMessage(content=SIGNAL_ANALYST_PROMPT),
            HumanMessage(content=f"""
Analyze this transaction signal and confirm the FactSheet:

Transaction ID: {signal.transaction_id}
User Claim: {signal.user_claim}
Bank Status: {signal.bank_status.value}
Ledger Status: {signal.ledger_status.value}
Amount: ${signal.amount}

Generated FactSheet:
- Bank Response: {fact_sheet.bank_api_response}
- Ledger Entry Exists: {fact_sheet.ledger_entry_exists}
- Data Consistency: {fact_sheet.data_consistency}

Confirm this analysis is accurate and add any additional observations.
""")
        ]
        
        try:
            response = llm.invoke(messages)
            # Add LLM analysis to messages for logging
            return {
                "fact_sheet": fact_sheet,
                "messages": [("Signal Analyst", f"FactSheet created. Analysis: {response.content}")]
            }
        except Exception as e:
            # Fallback to deterministic analysis
            pass
    
    return {
        "fact_sheet": fact_sheet,
        "messages": [(AGENT_NAMES["analyst"], f"FactSheet created. Consistency: {fact_sheet.data_consistency}")]
    }
