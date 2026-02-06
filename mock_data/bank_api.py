"""
Mock Bank API - Chaos Monkey for testing.
Simulates various bank responses including timeouts and failures.
"""

import random
from enum import Enum
from typing import Optional
from models.schemas import BankStatus, LedgerStatus, TransactionSignal
from datetime import datetime


class ChaosMode(str, Enum):
    """Chaos modes for the mock bank."""
    HAPPY_PATH = "happy_path"           # Always returns clear success/failure
    ADVERSARIAL = "adversarial"         # User lies, bank has truth
    AMBIGUOUS = "ambiguous"             # 504 timeouts, conflicting data
    RANDOM = "random"                   # Random chaos


class MockBankAPI:
    """
    Simulates a flaky bank API for testing the Circuit Breaker.
    """
    
    def __init__(self, chaos_mode: ChaosMode = ChaosMode.RANDOM):
        self.chaos_mode = chaos_mode
        self._pending_transactions = {}
    
    def get_transaction_status(self, transaction_id: str) -> BankStatus:
        """
        Get the status of a transaction.
        Behavior depends on chaos_mode.
        """
        if self.chaos_mode == ChaosMode.HAPPY_PATH:
            return BankStatus.FAILED  # Clear failure for refund
        
        elif self.chaos_mode == ChaosMode.ADVERSARIAL:
            return BankStatus.SUCCESS  # Transaction actually succeeded
        
        elif self.chaos_mode == ChaosMode.AMBIGUOUS:
            return BankStatus.TIMEOUT_504  # The trap!
        
        else:  # RANDOM
            return random.choice([
                BankStatus.SUCCESS,
                BankStatus.FAILED,
                BankStatus.TIMEOUT_504,
                BankStatus.PENDING
            ])


class MockLedger:
    """
    Simulates the internal ledger system.
    """
    
    def __init__(self, chaos_mode: ChaosMode = ChaosMode.RANDOM):
        self.chaos_mode = chaos_mode
        self._entries = {}
    
    def check_entry(self, transaction_id: str) -> LedgerStatus:
        """
        Check if a transaction exists in the ledger.
        """
        if self.chaos_mode == ChaosMode.HAPPY_PATH:
            return LedgerStatus.NOT_FOUND  # No entry = payment didn't go through
        
        elif self.chaos_mode == ChaosMode.ADVERSARIAL:
            return LedgerStatus.FOUND  # Entry exists = payment completed
        
        elif self.chaos_mode == ChaosMode.AMBIGUOUS:
            return LedgerStatus.NOT_FOUND  # Empty but bank state unknown
        
        else:  # RANDOM
            return random.choice([
                LedgerStatus.FOUND,
                LedgerStatus.NOT_FOUND,
                LedgerStatus.PENDING
            ])


def create_mock_signal(
    transaction_id: str,
    user_claim: str,
    amount: float,
    chaos_mode: ChaosMode = ChaosMode.RANDOM
) -> TransactionSignal:
    """
    Create a transaction signal using mock bank and ledger.
    """
    bank = MockBankAPI(chaos_mode)
    ledger = MockLedger(chaos_mode)
    
    return TransactionSignal(
        transaction_id=transaction_id,
        user_claim=user_claim,
        bank_status=bank.get_transaction_status(transaction_id),
        ledger_status=ledger.check_entry(transaction_id),
        amount=amount,
        timestamp=datetime.now()
    )
