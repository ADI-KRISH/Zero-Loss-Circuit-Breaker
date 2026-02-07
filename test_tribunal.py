"""
Sentinel: Test Suite
====================

Verifies the logic of the Multi-Agent Tribunal.
Tests the 3 core scenarios:
1. Happy Path (VIP User + Success) -> APPROVE
2. Fraud Attack (Low Trust + Failure) -> DENY
3. Timeout Trap (VIP User + Timeout) -> ESCALATE (Circuit Breaker)
"""

import sys
import os
from dotenv import load_dotenv

# Ensure we can import from root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_logic import TribunalBrain

# Load environment variables
load_dotenv()

def run_test(name, inputs, expected_verdict):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"INPUTS: {inputs}")
    print(f"{'='*60}")
    
    try:
        result = TribunalBrain.analyze(
            transaction_id="TEST-TX",
            amount=inputs["amount"],
            user_trust=inputs["user_trust"],
            network_status=inputs["network_status"]
        )
        
        verdict = result["verdict"]
        reason = result["reason"]
        
        print(f"VERDICT: {verdict}")
        print(f"REASON: {reason}")
        
        if verdict == expected_verdict:
            print(f"✅ PASS: Got {verdict}")
            return True
        else:
            print(f"❌ FAIL: Expected {expected_verdict}, Got {verdict}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("\n🛡️ RUNNING SENTINEL TEST SUITE\n")
    
    # Test 1: Happy Path
    t1 = run_test(
        "Happy Path (VIP Customer)",
        {"amount": 5000, "user_trust": 0.9, "network_status": "SUCCESS_200"},
        "APPROVE"
    )
    
    # Test 2: Simple Fraud
    t2 = run_test(
        "Simple Fraud (Low Trust + Bad Bank Reg)",
        {"amount": 5000, "user_trust": 0.1, "network_status": "FAILED_402"},
        "DENY"
    )
    
    # Test 3: The Timeout Trap (Circuit Breaker)
    t3 = run_test(
        "The Timeout Trap (Ambiguous State)",
        {"amount": 5000, "user_trust": 0.9, "network_status": "TIMEOUT_504"},
        "ESCALATE"
    )
    
    print("\n" + "="*60)
    if t1 and t2 and t3:
        print("🎉 ALL SYSTEMS GO: SENTINEL IS READY")
    else:
        print("⚠️ SOME TESTS FAILED")
    print("="*60 + "\n")
