"""
Zero-Loss Circuit Breaker: FastAPI Middleware
==============================================

Exposes TribunalBrain as a REST API for the Merchant Store.

HOW TO RUN THE COMPLETE SYSTEM:
================================
Terminal 1: uvicorn api:app --reload
Terminal 2: streamlit run dashboard.py --server.port 8501
Terminal 3: streamlit run merchant_store.py --server.port 8502
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import json
import os

from core_logic import TribunalBrain

# ============================================================================
# CONFIGURATION
# ============================================================================

app = FastAPI(
    title="Zero-Loss Circuit Breaker API",
    description="Multi-Agent Tribunal for Payment Security",
    version="2.0.0"
)

# Enable CORS for Streamlit apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database file
DB_FILE = "transactions_db.json"


# ============================================================================
# MODELS
# ============================================================================

class WebhookPayload(BaseModel):
    """Incoming webhook from merchant store."""
    transaction_id: str = Field(..., description="Unique transaction ID")
    amount: float = Field(..., description="Transaction amount", ge=0)
    user_id: str = Field(..., description="User identifier")
    user_trust: float = Field(..., description="Trust score 0-1", ge=0, le=1)
    status: str = Field(..., description="Network status code")

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "tx_001",
                "amount": 199.99,
                "user_id": "cust_12345",
                "user_trust": 0.85,
                "status": "TIMEOUT_504"
            }
        }


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def load_db() -> list:
    """Load transactions from JSON."""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_db(transactions: list):
    """Save transactions to JSON."""
    with open(DB_FILE, "w") as f:
        json.dump(transactions, f, indent=2)


def append_transaction(record: dict):
    """Append a transaction to the database."""
    transactions = load_db()
    transactions.append(record)
    save_db(transactions)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Zero-Loss Circuit Breaker API",
        "version": "2.0.0",
        "status": "online",
        "endpoints": {
            "webhook": "POST /webhook",
            "transactions": "GET /transactions",
            "stats": "GET /stats"
        }
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/webhook")
async def process_webhook(payload: WebhookPayload):
    """
    Process incoming payment webhook from merchant store.
    
    Runs the transaction through TribunalBrain and saves result.
    """
    # Run through TribunalBrain
    result = TribunalBrain.analyze(
        amount=payload.amount,
        user_trust=payload.user_trust,
        network_status=payload.status
    )
    
    # Create full record
    record = {
        "transaction_id": payload.transaction_id,
        "user_id": payload.user_id,
        "amount": payload.amount,
        "user_trust": payload.user_trust,
        "network_status": payload.status,
        "verdict": result["verdict"],
        "reason": result["reason"],
        "risk_score": result["risk_score"],
        "circuit_breaker": result["circuit_breaker"],
        "logs": result["logs"],
        "timestamp": datetime.now().isoformat()
    }
    
    # Save to database
    append_transaction(record)
    
    # Return verdict to caller
    return {
        "transaction_id": payload.transaction_id,
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


@app.get("/stats")
async def get_stats():
    """Get statistics."""
    transactions = load_db()
    
    total = len(transactions)
    approved = sum(1 for t in transactions if t.get("verdict") == "APPROVE")
    denied = sum(1 for t in transactions if t.get("verdict") == "DENY")
    escalated = sum(1 for t in transactions if t.get("verdict") == "ESCALATE")
    
    # Money saved = sum of escalated + denied transactions
    money_saved = sum(
        t.get("amount", 0) 
        for t in transactions 
        if t.get("verdict") in ["ESCALATE", "DENY"]
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
    """Clear all transactions (for demo reset)."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
