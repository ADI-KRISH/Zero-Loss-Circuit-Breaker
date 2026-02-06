"""
Test Scenarios for the Zero-Loss Circuit Breaker Demo.
Pre-built scenarios to demonstrate all three paths.
"""

from datetime import datetime
from models.schemas import TransactionSignal, BankStatus, LedgerStatus


def get_happy_path_scenario() -> TransactionSignal:
    """
    SCENARIO A: The Easy Win (Refund)
    - Bank says FAILED
    - Ledger shows NOT_FOUND
    - Expected Result: REFUND (consensus reached)
    """
    return TransactionSignal(
        transaction_id="TXN-HAPPY-001",
        user_claim="I was charged $99.99 but got an error message and never received my order confirmation. Please help!",
        bank_status=BankStatus.FAILED,
        ledger_status=LedgerStatus.NOT_FOUND,
        amount=99.99,
        timestamp=datetime.now()
    )


def get_adversarial_scenario() -> TransactionSignal:
    """
    SCENARIO B: The Fraudster (Deny)
    - Bank says SUCCESS
    - Ledger shows FOUND
    - User claims it failed (lying)
    - Expected Result: DENY (fraud detected)
    """
    return TransactionSignal(
        transaction_id="TXN-FRAUD-002",
        user_claim="The payment failed! I didn't receive anything! Give me my money back NOW!",
        bank_status=BankStatus.SUCCESS,
        ledger_status=LedgerStatus.FOUND,
        amount=499.99,
        timestamp=datetime.now()
    )


def get_circuit_breaker_scenario() -> TransactionSignal:
    """
    SCENARIO C: The Circuit Breaker (THE WINNING MOMENT)
    - Bank returns 504 GATEWAY TIMEOUT
    - Ledger shows NOT_FOUND
    - Transaction state is INDETERMINATE
    - Expected Result: ESCALATE (Strategic Refusal)
    """
    return TransactionSignal(
        transaction_id="TXN-AMBIGUOUS-003",
        user_claim="I tried to buy a laptop for $1,299. The page just showed 'loading' forever and then said 'Something went wrong'. Was I charged or not?!",
        bank_status=BankStatus.TIMEOUT_504,
        ledger_status=LedgerStatus.NOT_FOUND,
        amount=1299.99,
        timestamp=datetime.now()
    )


def get_pending_scenario() -> TransactionSignal:
    """
    SCENARIO D: Pending Transaction
    - Bank says PENDING
    - Ledger shows PENDING
    - Expected Result: ESCALATE (wait for completion)
    """
    return TransactionSignal(
        transaction_id="TXN-PENDING-004",
        user_claim="It's been 5 minutes and my payment is still processing. Should I try again?",
        bank_status=BankStatus.PENDING,
        ledger_status=LedgerStatus.PENDING,
        amount=75.00,
        timestamp=datetime.now()
    )


def get_conflicting_scenario() -> TransactionSignal:
    """
    SCENARIO E: Conflicting Data
    - Bank says SUCCESS
    - Ledger shows NOT_FOUND (inconsistent!)
    - Expected Result: ESCALATE (data conflict)
    """
    return TransactionSignal(
        transaction_id="TXN-CONFLICT-005",
        user_claim="I'm confused - I got a 'payment successful' email but the order isn't in my account.",
        bank_status=BankStatus.SUCCESS,
        ledger_status=LedgerStatus.NOT_FOUND,
        amount=199.99,
        timestamp=datetime.now()
    )


# Dictionary of all scenarios for easy access
ALL_SCENARIOS = {
    "happy_path": get_happy_path_scenario,
    "adversarial": get_adversarial_scenario,
    "circuit_breaker": get_circuit_breaker_scenario,
    "pending": get_pending_scenario,
    "conflicting": get_conflicting_scenario
}
