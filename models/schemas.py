"""
Pydantic Schemas for Zero-Loss Circuit Breaker.
Defines the data structures for transaction signals, agent votes, and verdicts.
"""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional, List
from pydantic import BaseModel, Field


class BankStatus(str, Enum):
    """Possible states from the Bank API."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT_504 = "TIMEOUT_504"
    PENDING = "PENDING"


class LedgerStatus(str, Enum):
    """Possible states from the internal Ledger."""
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    PENDING = "PENDING"


class Decision(str, Enum):
    """Possible agent/system decisions."""
    REFUND = "REFUND"
    DENY = "DENY"
    UNCERTAIN = "UNCERTAIN"
    ESCALATE = "ESCALATE"


class TransactionSignal(BaseModel):
    """
    The input signal representing the current state of a disputed transaction.
    This is gathered by the Signal Analyst agent.
    """
    transaction_id: str = Field(..., description="Unique identifier for the transaction")
    user_claim: str = Field(..., description="The user's complaint or claim text")
    bank_status: BankStatus = Field(..., description="Status returned by the Bank API")
    ledger_status: LedgerStatus = Field(..., description="Status from internal ledger")
    amount: float = Field(..., description="Transaction amount in currency")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the dispute was raised")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "TXN-12345",
                "user_claim": "I was charged but never received my product!",
                "bank_status": "TIMEOUT_504",
                "ledger_status": "NOT_FOUND",
                "amount": 99.99,
                "timestamp": "2026-02-06T12:00:00"
            }
        }


class FactSheet(BaseModel):
    """
    Objective facts extracted by the Signal Analyst.
    No opinions, just raw truth from the data sources.
    """
    transaction_id: str
    bank_api_response: str = Field(..., description="Raw response summary from bank")
    ledger_entry_exists: bool
    ledger_state: Optional[str] = None
    data_consistency: Literal["CONSISTENT", "CONFLICTING", "INDETERMINATE"]
    raw_signals: TransactionSignal


class AgentArgument(BaseModel):
    """
    An argument made by an agent during the debate.
    """
    agent_name: str
    position: Decision
    reasoning: str = Field(..., description="The logical argument supporting the position")
    evidence: List[str] = Field(default_factory=list, description="Key facts cited")
    confidence: float = Field(..., ge=0, le=100, description="Confidence score 0-100")


class AgentVote(BaseModel):
    """
    The final vote submitted by an agent after the debate rounds.
    """
    agent_name: str
    vote: Decision
    confidence: float = Field(..., ge=0, le=100)
    final_reasoning: str
    veto_triggered: bool = Field(default=False, description="If True, this agent is blocking the action")


class DebateLog(BaseModel):
    """
    Complete record of the multi-round debate between agents.
    """
    round_1_arguments: List[AgentArgument] = Field(default_factory=list)
    round_2_rebuttals: List[AgentArgument] = Field(default_factory=list)
    round_3_votes: List[AgentVote] = Field(default_factory=list)


class Verdict(BaseModel):
    """
    The final output of the Zero-Loss Circuit Breaker system.
    """
    transaction_id: str
    decision: Decision
    confidence: float = Field(..., ge=0, le=100)
    reasoning: str
    circuit_breaker_triggered: bool = Field(default=False)
    escalation_reason: Optional[str] = None
    debate_summary: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "TXN-12345",
                "decision": "ESCALATE",
                "confidence": 45.0,
                "reasoning": "Agents could not reach consensus on the location of funds.",
                "circuit_breaker_triggered": True,
                "escalation_reason": "Bank API timeout (504) - transaction state indeterminate",
                "debate_summary": "Advocate argued for refund (65% conf), Risk Officer vetoed (85% risk conf)"
            }
        }
