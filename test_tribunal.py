"""
Simple test script to verify the tribunal system works.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from models.schemas import Decision
from mock_data.scenarios import (
    get_happy_path_scenario,
    get_adversarial_scenario,
    get_circuit_breaker_scenario
)
from core.graph import run_tribunal


def test_scenario(name: str, signal_fn):
    """Test a single scenario."""
    print(f"\n{'='*60}")
    print(f"TESTING: {name}")
    print(f"{'='*60}")
    
    signal = signal_fn()
    print(f"Input: Bank={signal.bank_status.value}, Ledger={signal.ledger_status.value}")
    
    try:
        result = run_tribunal(signal)
        verdict = result.get("verdict")
        
        if verdict:
            print(f"Decision: {verdict.decision.value}")
            print(f"Confidence: {verdict.confidence:.1f}%")
            print(f"Circuit Breaker: {verdict.circuit_breaker_triggered}")
            print(f"Reasoning: {verdict.reasoning[:100]}...")
            if verdict.escalation_reason:
                print(f"Escalation: {verdict.escalation_reason}")
            return verdict
        else:
            print("ERROR: No verdict returned")
            return None
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("ZERO-LOSS CIRCUIT BREAKER - Test Suite")
    print("="*60)
    
    # Test 1: Happy Path - Should REFUND
    v1 = test_scenario("Happy Path (Expected: REFUND)", get_happy_path_scenario)
    
    # Test 2: Adversarial - Should DENY
    v2 = test_scenario("Adversarial (Expected: DENY)", get_adversarial_scenario)
    
    # Test 3: Circuit Breaker - Should ESCALATE
    v3 = test_scenario("Circuit Breaker (Expected: ESCALATE)", get_circuit_breaker_scenario)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    results = [
        ("Happy Path", v1, Decision.REFUND),
        ("Adversarial", v2, Decision.DENY),
        ("Circuit Breaker", v3, Decision.ESCALATE)
    ]
    
    all_passed = True
    for name, verdict, expected in results:
        if verdict and verdict.decision == expected:
            print(f"✅ {name}: PASS ({verdict.decision.value} == {expected.value})")
        elif verdict:
            print(f"⚠️  {name}: PARTIAL ({verdict.decision.value} != {expected.value})")
            all_passed = False
        else:
            print(f"❌ {name}: FAIL (No verdict)")
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  Some tests did not match expected behavior")
