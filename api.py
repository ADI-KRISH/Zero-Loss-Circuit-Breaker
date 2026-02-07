"""
Sentinel: FastAPI Middleware
============================

Exposes TribunalBrain via REST API.
Saves full logs to transactions_db.json.

HOW TO RUN THE COMPLETE SYSTEM:
================================
Terminal 1: uvicorn api:app --reload
Terminal 2: streamlit run dashboard.py --server.port 8501
Terminal 3: streamlit run merchant_store.py --server.port 8502
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import json
import os
import uuid
import threading
from contextlib import contextmanager

from core_logic import TribunalBrain

# File Lock for Thread Safety
DB_LOCK = threading.Lock()

# ============================================================================
# CONFIGURATION
# ============================================================================

app = FastAPI(
    title="Sentinel API",
    description="Multi-Agent Tribunal for Payment Security",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "transactions_db.json"


# ============================================================================
# MODELS
# ============================================================================

class WebhookPayload(BaseModel):
    """Incoming webhook from merchant store."""
    transaction_id: Optional[str] = Field(None, description="Transaction ID (auto-generated if not provided)")
    amount: float = Field(..., description="Transaction amount", ge=0)
    user_id: str = Field(..., description="User identifier")
    user_trust: float = Field(..., description="Trust score 0-1", ge=0, le=1)
    status: str = Field(..., description="Network status (SUCCESS_200, TIMEOUT_504, FAILED_402)")

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "TX-001",
                "amount": 199.99,
                "user_id": "cust_12345",
                "user_trust": 0.9,
                "status": "TIMEOUT_504"
            }
        }


# ============================================================================
# DATABASE
# ============================================================================

def load_db() -> list:
    if not os.path.exists(DB_FILE):
        return []
    try:
        with DB_LOCK:
            with open(DB_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
    except json.JSONDecodeError:
        print(f"Error: {DB_FILE} is corrupted. Returning empty list.")
        return []
    except Exception as e:
        print(f"Error loading DB: {e}")
        return []


def save_db(transactions: list):
    with open(DB_FILE, "w") as f:
        json.dump(transactions, f, indent=2)


def append_transaction(record: dict):
    with DB_LOCK:
        # Load inside the lock to prevent lost updates
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    content = f.read().strip()
                    transactions = json.loads(content) if content else []
            except (json.JSONDecodeError, FileNotFoundError):
                transactions = []
        else:
            transactions = []
        
        transactions.append(record)
        
        # Log Rotation: Keep last 1000 records to prevent disk overflow
        if len(transactions) > 1000:
            transactions = transactions[-1000:]
        
        with open(DB_FILE, "w") as f:
            json.dump(transactions, f, indent=2)


# ============================================================================
# ENDPOINTS
# ============================================================================

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Verify critical environment variables on startup."""
    if not os.getenv("OPENAI_API_KEY"):
        print("\n\n🚨🚨🚨 CRITICAL ERROR: OPENAI_API_KEY is missing! 🚨🚨🚨\n")
        # We warn loudly but don't exit to allow hot-reloading fixes

@app.get("/")
async def root():
    return {
        "service": "Sentinel API",
        "version": "3.0.0",
        "status": "online",
        "endpoints": {
            "webhook": "POST /webhook",
            "transactions": "GET /transactions",
            "transaction": "GET /transaction/{id}",
            "stats": "GET /stats"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/webhook")
async def process_webhook(payload: WebhookPayload):
    """
    Process payment webhook through TribunalBrain.
    Saves full result including debate logs.
    """
    # Generate transaction ID if not provided
    tx_id = payload.transaction_id or f"TX-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    
    # Edge Case: Zero or Negative Amount (Double check)
    if payload.amount <= 0:
        return {
            "transaction_id": tx_id,
            "verdict": "DENY",
            "reason": "Invalid transaction amount (<= 0)",
            "circuit_breaker": False
        }

    # Run through TribunalBrain (with deep logging)
    result = TribunalBrain.analyze(
        transaction_id=tx_id,
        amount=payload.amount,
        user_trust=payload.user_trust,
        network_status=payload.status
    )
    
    # Create full record
    record = {
        "transaction_id": tx_id,
        "user_id": payload.user_id,
        "amount": payload.amount,
        "user_trust": payload.user_trust,
        "network_status": payload.status,
        "verdict": result["verdict"],
        "reason": result["reason"],
        "risk_score": result["risk_score"],
        "circuit_breaker": result["circuit_breaker"],
        "advocate_vote": result["advocate_vote"],
        "risk_vote": result["risk_vote"],
        "logs": result["logs"],
        "timestamp": datetime.now().isoformat()
    }
    
    # Save to database
    append_transaction(record)
    
    # Return verdict
    return {
        "transaction_id": tx_id,
        "verdict": result["verdict"],
        "reason": result["reason"],
        "circuit_breaker": result["circuit_breaker"]
    }


@app.get("/transactions")
async def get_transactions(limit: int = 100):
    """Get all transactions."""
    transactions = load_db()
    return {
        "count": len(transactions),
        "transactions": list(reversed(transactions[-limit:]))
    }


@app.get("/transaction/{tx_id}")
async def get_transaction(tx_id: str):
    """Get a specific transaction with full logs."""
    transactions = load_db()
    for tx in transactions:
        if tx.get("transaction_id") == tx_id:
            return tx
    raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found")


@app.get("/stats")
async def get_stats():
    """Get statistics."""
    transactions = load_db()
    
    total = len(transactions)
    approved = sum(1 for t in transactions if t.get("verdict") == "APPROVE")
    denied = sum(1 for t in transactions if t.get("verdict") == "DENY")
    escalated = sum(1 for t in transactions if t.get("verdict") == "ESCALATE")
    
    money_saved = sum(
        t.get("amount", 0) 
        for t in transactions 
        if t.get("circuit_breaker", False)
    )
    
    return {
        "total": total,
        "approved": approved,
        "denied": denied,
        "escalated": escalated,
        "money_saved": money_saved
    }


@app.delete("/transactions")
async def clear_transactions():
    """Clear all transactions."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
