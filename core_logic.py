"""
Sentinel: The Shared Brain (Core Logic)
========================================

Multi-Agent Tribunal with Deep Logging using LANGGRAPH.
Every state change, thought, and argument is captured in the graph state.

HOW TO RUN THE COMPLETE SYSTEM:
================================
Terminal 1: uvicorn api:app --reload
Terminal 2: streamlit run dashboard.py --server.port 8501
Terminal 3: streamlit run merchant_store.py --server.port 8502
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TypedDict, Annotated
from datetime import datetime
from enum import Enum
import operator
import os
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Import Agents
from agents.advocate import get_advocate_decision
from agents.risk_officer import get_risk_decision
from agents.judge import get_judge_decision

# Load environment variables
load_dotenv()

# Initialize LLM with Timeout
try:
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.2,
        request_timeout=20  # Hard timeout to prevent silent hanging
    )
except Exception as e:
    print(f"CRITICAL WARNING: LLM not initialized: {e}")
    llm = None


# ============================================================================
# LOGGING STRUCTURES
# ============================================================================

@dataclass
class LogEntry:
    """A single log entry."""
    log_type: str
    agent: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3])
    
    def to_dict(self) -> dict:
        return {
            "type": self.log_type,
            "agent": self.agent,
            "message": self.message,
            "timestamp": self.timestamp
        }


# ============================================================================
# LANGGRAPH STATE
# ============================================================================

def merge_logs(left: List[dict], right: List[dict]) -> List[dict]:
    """Reducer to append logs."""
    if right is None:
        return left
    return left + right

class TribunalState(TypedDict):
    # Inputs
    transaction_id: str
    amount: float
    user_trust: float
    network_status: str
    
    # Agent Outputs
    advocate_vote: Optional[str]
    advocate_stance: Optional[str]
    
    risk_vote: Optional[str]
    risk_score: Optional[float]
    risk_stance: Optional[str]
    
    # Final Verdict
    verdict: Optional[str]
    reason: Optional[str]
    circuit_breaker: Optional[bool]
    
    # Shared Logs (Append-only)
    logs: Annotated[List[dict], merge_logs]


# ============================================================================
# AGENT NODES
# ============================================================================

def advocate_node(state: TribunalState):
    """The Customer Advocate Agent."""
    trust = state["user_trust"]
    amount = state["amount"]
    
    result = get_advocate_decision(trust, amount, llm)
    
    # Create logs
    new_logs = [
        LogEntry("THOUGHT", "Advocate", result.get("thought", "")).to_dict(),
        LogEntry("SPEAK", "Advocate", result.get("stance", "")).to_dict()
    ]
    
    return {
        "advocate_vote": result.get("vote", "WAIT"),
        "advocate_stance": result.get("stance", ""),
        "logs": new_logs
    }


def risk_node(state: TribunalState):
    """The Risk Officer Agent."""
    status = state["network_status"]
    
    result = get_risk_decision(status, llm)
    
    new_logs = [
        LogEntry("THOUGHT", "Risk Officer", result.get("thought", "")).to_dict(),
        LogEntry("SPEAK", "Risk Officer", result.get("stance", "")).to_dict()
    ]
    
    return {
        "risk_vote": result.get("vote", "OBJECTION"),
        "risk_score": result.get("score", 100),
        "risk_stance": result.get("stance", ""),
        "logs": new_logs
    }


def judge_node(state: TribunalState):
    """The Judge Agent."""
    adv_vote = state["advocate_vote"]
    risk_vote = state["risk_vote"]
    
    result = get_judge_decision(adv_vote, risk_vote, llm)
    
    new_logs = [
        LogEntry("JUDGE", "Judge", result.get("thought", "")).to_dict(),
        LogEntry("VERDICT", "Judge", f"{result.get('verdict', 'ESCALATE')} - {result.get('reason', '')}").to_dict()
    ]
    
    return {
        "verdict": result.get("verdict", "ESCALATE"),
        "reason": result.get("reason", "Graph Error"),
        "circuit_breaker": result.get("circuit_breaker", True),
        "logs": new_logs
    }


# ============================================================================
# TRIBUNAL BRAIN (GRAPH RUNNER)
# ============================================================================

class TribunalBrain:
    """Wrapper to run the LangGraph Tribunal."""
    
    @classmethod
    def analyze(cls, transaction_id: str, amount: float, user_trust: float, network_status: str) -> dict:
        """Run the graph."""
        
        # 1. Setup Graph
        workflow = StateGraph(TribunalState)
        
        workflow.add_node("advocate", advocate_node)
        workflow.add_node("risk", risk_node)
        workflow.add_node("judge", judge_node)
        
        workflow.set_entry_point("advocate")
        workflow.add_edge("advocate", "risk")
        workflow.add_edge("risk", "judge")
        workflow.add_edge("judge", END)
        
        app = workflow.compile()
        
        # 2. Initial Logs
        init_logs = [
            LogEntry("SYSTEM", "Tribunal", f"Tribunal activated for Tx {transaction_id}").to_dict(),
            LogEntry("SYSTEM", "Tribunal", f"Loading Profile: Trust {user_trust:.0%}").to_dict(),
            LogEntry("SYSTEM", "Tribunal", f"Network Signal: {network_status}").to_dict()
        ]
        
        # 3. Invoke
        inputs = {
            "transaction_id": transaction_id,
            "amount": amount,
            "user_trust": user_trust,
            "network_status": network_status,
            "logs": init_logs
        }
        
        final_state = app.invoke(inputs)
        
        # 4. Format Output
        return {
            "verdict": final_state.get("verdict", "ESCALATE"),
            "reason": final_state.get("reason", "Graph Error"),
            "risk_score": final_state.get("risk_score", 100),
            "circuit_breaker": final_state.get("circuit_breaker", True),
            "logs": final_state.get("logs", []),
            "advocate_vote": final_state.get("advocate_vote", "WAIT"),
            "risk_vote": final_state.get("risk_vote", "OBJECTION")
        }


# Quick test
if __name__ == "__main__":
    print("=== Testing LangGraph Tribunal ===\n")
    res = TribunalBrain.analyze("TEST-LG", 5000, 0.9, "TIMEOUT_504")
    print(f"Verdict: {res['verdict']}")
    print(f"Reason: {res['reason']}")
    print("-" * 20)
    for log in res['logs']:
        print(f"[{log['type']}] {log['agent']}: {log['message']}")
