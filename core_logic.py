"""
Zero-Loss Circuit Breaker: Core Logic (The Shared Brain)
========================================================

This module contains the Multi-Agent Tribunal logic shared by:
- dashboard.py (Ops Console - Simulation Gym)
- api.py (Middleware for merchant_store.py)

HOW TO RUN THE COMPLETE SYSTEM:
================================
Terminal 1: uvicorn api:app --reload
Terminal 2: streamlit run dashboard.py --server.port 8501
Terminal 3: streamlit run merchant_store.py --server.port 8502
"""

from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime


@dataclass
class TribunalResult:
    """Result of tribunal deliberation."""
    verdict: str  # "APPROVE", "DENY", "ESCALATE"
    reason: str
    logs: List[str]
    risk_score: float
    circuit_breaker: bool
    
    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "logs": self.logs,
            "risk_score": self.risk_score,
            "circuit_breaker": self.circuit_breaker,
            "timestamp": datetime.now().isoformat()
        }


class TribunalBrain:
    """
    The Multi-Agent Tribunal Brain.
    
    Agents:
    - Advocate: Trusts high-trust users
    - Risk Officer: Checks network status (has VETO power)
    - Judge: Makes final decision
    """
    
    @classmethod
    def analyze(
        cls,
        amount: float,
        user_trust: float,
        network_status: str
    ) -> dict:
        """
        Analyze a transaction through the tribunal.
        
        Args:
            amount: Transaction amount in dollars
            user_trust: Trust score (0.0 - 1.0)
            network_status: One of "SUCCESS_200", "TIMEOUT_504", "FAILED_402"
        
        Returns:
            dict with verdict, reason, logs, risk_score, circuit_breaker
        """
        logs = []
        
        # ================================================================
        # AGENT A: User Advocate
        # ================================================================
        if user_trust >= 0.8:
            advocate_vote = "APPROVE"
            advocate_msg = f"🧑‍💼 **Advocate**: High trust user ({user_trust:.0%}). I vote **APPROVE**."
        else:
            advocate_vote = "WAIT"
            advocate_msg = f"🧑‍💼 **Advocate**: Moderate trust ({user_trust:.0%}). I vote **WAIT** for more data."
        logs.append(advocate_msg)
        
        # ================================================================
        # AGENT B: Risk Officer
        # ================================================================
        status = network_status.upper()
        
        if "504" in status or "TIMEOUT" in status:
            risk_vote = "BLOCK"
            risk_msg = "👮 **Risk Officer**: ⛔ Network returned `504 TIMEOUT`. Transaction state is **UNKNOWN**. I vote **BLOCK** to prevent double-spend!"
            risk_score = 95
        elif "402" in status or "FAILED" in status or "DECLINED" in status:
            risk_vote = "DENY"
            risk_msg = "👮 **Risk Officer**: Payment was declined by the bank. I vote **DENY**."
            risk_score = 80
        elif "200" in status or "SUCCESS" in status:
            risk_vote = "APPROVE"
            risk_msg = "👮 **Risk Officer**: Payment confirmed (200 OK). No risk detected. I vote **APPROVE**."
            risk_score = 10
        else:
            risk_vote = "BLOCK"
            risk_msg = f"👮 **Risk Officer**: Unknown status `{network_status}`. I vote **BLOCK** for safety."
            risk_score = 70
        logs.append(risk_msg)
        
        # ================================================================
        # THE JUDGE: Final Verdict
        # ================================================================
        if risk_vote == "DENY":
            verdict = "DENY"
            reason = "Payment declined by bank. Transaction cannot proceed."
            judge_msg = f"⚖️ **Judge**: Risk Officer confirms failure. **DENIED**."
            circuit_breaker = False
        
        elif advocate_vote == "APPROVE" and risk_vote == "BLOCK":
            # THE TRAP: High trust user BUT network is ambiguous
            verdict = "ESCALATE"
            reason = "Circuit Breaker Triggered! High trust user but network state unknown. Human review required."
            judge_msg = f"⚖️ **Judge**: 🔒 **CIRCUIT BREAKER TRIGGERED!** Advocate wants to approve, but Risk detected ambiguity. **ESCALATING** to human review."
            circuit_breaker = True
        
        elif advocate_vote == "APPROVE" and risk_vote == "APPROVE":
            verdict = "APPROVE"
            reason = "Both agents agree. Transaction is safe to proceed."
            judge_msg = f"⚖️ **Judge**: Both agents agree. **APPROVED**."
            circuit_breaker = False
        
        elif advocate_vote == "WAIT" and risk_vote == "BLOCK":
            verdict = "ESCALATE"
            reason = "Low confidence + ambiguous network. Escalating for safety."
            judge_msg = f"⚖️ **Judge**: Insufficient trust and network is unclear. **ESCALATING**."
            circuit_breaker = True
        
        elif advocate_vote == "WAIT" and risk_vote == "APPROVE":
            verdict = "APPROVE"
            reason = "Network confirmed success. Proceeding despite moderate trust."
            judge_msg = f"⚖️ **Judge**: Network confirmed. **APPROVED** with monitoring."
            circuit_breaker = False
        
        else:
            verdict = "ESCALATE"
            reason = "Agents could not reach consensus. Human review required."
            judge_msg = f"⚖️ **Judge**: No consensus. **ESCALATING**."
            circuit_breaker = True
        
        logs.append(judge_msg)
        
        return TribunalResult(
            verdict=verdict,
            reason=reason,
            logs=logs,
            risk_score=risk_score,
            circuit_breaker=circuit_breaker
        ).to_dict()


# Quick test
if __name__ == "__main__":
    print("=== Testing TribunalBrain ===\n")
    
    # Test 1: Happy path
    result = TribunalBrain.analyze(5000, 0.9, "SUCCESS_200")
    print(f"Test 1 (Happy): {result['verdict']}")
    
    # Test 2: The Trap
    result = TribunalBrain.analyze(5000, 0.9, "TIMEOUT_504")
    print(f"Test 2 (Trap): {result['verdict']} - Circuit Breaker: {result['circuit_breaker']}")
    
    # Test 3: Declined
    result = TribunalBrain.analyze(5000, 0.5, "FAILED_402")
    print(f"Test 3 (Declined): {result['verdict']}")
