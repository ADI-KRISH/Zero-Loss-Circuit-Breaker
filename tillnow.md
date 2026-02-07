# Zero-Loss Circuit Breaker: Development Log

## Project Overview
Built a Multi-Agent Tribunal System for autonomous payment dispute resolution demonstrating "Strategic Refusal" for the EpochOn 2.0 Hackathon (S4 & S6 Track: Multi-Agent Systems).

---

## Phase 1: Architecture Design

### What Was Done
1. Created `implementation_plan.md` with:
   - 4 Agent Personas (Signal Analyst, User Advocate, Risk Officer, Judge)
   - Active Debate Protocol (3 rounds)
   - Circuit Breaker Logic thresholds
   - Tech stack decision: LangGraph + OpenAI

2. Designed the refusal equation:
   - Low Confidence < 40% → ESCALATE
   - Consensus < 60% → ESCALATE
   - Risk Officer VETO → ESCALATE
   - 504 TIMEOUT → ESCALATE

---

## Phase 2: Project Initialization

### Files Created
```
zero_loss_circuit_breaker/
├── requirements.txt
├── .env (with OpenAI API key)
├── core/__init__.py
├── agents/__init__.py
├── models/__init__.py
└── mock_data/__init__.py
```

### Change: Switched from Gemini to OpenAI
**Reason**: User provided OpenAI API key
**Files Modified**: `requirements.txt`
```diff
- langchain-google-genai>=1.0.0
+ langchain-openai>=0.1.0
+ openai>=1.0.0
```

---

## Phase 3: Core Implementation

### Files Created
- `models/schemas.py` - Pydantic models (TransactionSignal, FactSheet, AgentVote, Verdict)
- `core/state.py` - LangGraph state definitions
- `core/prompts.py` - System prompts for all agents
- `core/graph.py` - LangGraph workflow

### Error 1: LangGraph Message Channel
**Error**: `ValueError: Unexpected message type: 'Signal Analyst'`
**Cause**: Used `add_messages` reducer which expects LangChain message types
**Fix**: Changed to simple list reducer
```python
# Before
messages: Annotated[list, add_messages]

# After  
def merge_messages(existing, new):
    return existing + new
messages: Annotated[List[Tuple[str, str]], merge_messages]
```

---

## Phase 4: Agent Implementation

### Files Created
- `agents/analyst.py` - Signal Analyst (fact extraction)
- `agents/advocate.py` - User Advocate (customer-focused)
- `agents/risk_officer.py` - Risk Officer (skeptic with VETO)
- `agents/judge.py` - Final arbiter

### Error 2: Wrong Import in Agents
**Error**: `NameError: name 'ChatGoogleGenerativeAI' is not defined`
**Cause**: Import said `langchain_google_genai` but we use OpenAI
**Fix**: Changed all agent files:
```python
# Before
from langchain_google_genai import ChatGoogleGenerativeAI

# After
from langchain_openai import ChatOpenAI
```
**Files Fixed**: analyst.py, advocate.py, risk_officer.py, judge.py

---

## Phase 5: Testing & Debugging

### Test Results (Initial)
| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Happy Path | REFUND | REFUND | ✅ PASS |
| Adversarial | DENY | ESCALATE | ⚠️ PARTIAL |
| Circuit Breaker | ESCALATE | ESCALATE | ✅ PASS |

### Error 3: Adversarial Case Not Working
**Problem**: Advocate was pushing REFUND even when data clearly showed SUCCESS+FOUND
**Root Cause**: In `build_round2_rebuttal()`, the advocate always challenged Risk Officer's DENY

**Fix in advocate.py**:
```python
# Added fraud detection at start of rebuttal
is_clear_fraud = (fact_sheet.data_consistency == "CONSISTENT" and 
                  fact_sheet.ledger_entry_exists)

if is_clear_fraud:
    # Advocate concedes when evidence is overwhelming
    position = Decision.DENY
    confidence = 85.0
    reasoning = "I must concede. Evidence is against user claim."
```

### Error 4: Duplicate Evidence Assignment
**Problem**: Evidence variable was being overwritten after all if/elif/else blocks
**Fix**: Removed the duplicate assignment

### Final Test Results
| Scenario | Expected | Actual | Confidence | Status |
|----------|----------|--------|------------|--------|
| Happy Path | REFUND | REFUND | 80.0% | ✅ PASS |
| Adversarial | DENY | DENY | 77.5% | ✅ PASS |
| Circuit Breaker | ESCALATE | ESCALATE | Circuit Breaker | ✅ PASS |

---

## Phase 6: Frontend Dashboard (Streamlit)

### Files Created
- `app.py` - The main Streamlit application
- `FRONTEND.md` - Technical documentation for the dashboard

### Features Implemented
1. **Live Simulation Page**:
   - Visual debate with colored avatars
   - Real-time message streaming simulation
   - Verdict Banners (Green for Refund/Deny, Flashing Yellow for Circuit Breaker)
   
2. **Escalation Desk Page**:
   - Queue management for triggered circuit breakers
   - "Force Refund" / "Force Deny" buttons for humans
   - Expandable details showing conflicting stats

### Dependencies Added
- `streamlit` added to `requirements.txt`

---

## Summary of All Changes Made

### Import Fixes
- `analyst.py` line 7: `langchain_google_genai` → `langchain_openai`
- `advocate.py` line 8: `langchain_google_genai` → `langchain_openai`
- `risk_officer.py` line 8: `langchain_google_genai` → `langchain_openai`
- `judge.py` line 7: `langchain_google_genai` → `langchain_openai`

### Type Hint Fixes
- All `ChatGoogleGenerativeAI` → `ChatOpenAI` in function signatures

### Logic Fixes
- `core/state.py`: Replaced `add_messages` with custom `merge_messages` reducer
- `agents/advocate.py`: Added fraud detection in round 1 and round 2 logic
- `agents/advocate.py`: Removed duplicate evidence assignment

---

## How to Run

```bash
cd zero_loss_circuit_breaker
pip install -r requirements.txt

# Run all tests
python test_tribunal.py

# Interactive demo
python main.py --interactive

# Single scenario
python main.py --scenario circuit
```

---

## Key Files Summary

| File | Purpose | Lines |
|------|---------|-------|
| main.py | CLI demo runner | ~260 |
| core/graph.py | LangGraph workflow | ~220 |
| agents/advocate.py | User advocate logic | ~300 |
| agents/risk_officer.py | Risk officer with VETO | ~290 |
| agents/judge.py | Circuit breaker logic | ~170 |
| models/schemas.py | Pydantic models | ~115 |

---

## Final Status: ✅ COMPLETE

All three scenarios working:
1. **Happy Path**: Consensus REFUND (80% confidence)
2. **Adversarial**: Consensus DENY (77.5% confidence)  
3. **Circuit Breaker**: Strategic Refusal ESCALATE (50% consensus → triggered)

---

## Phase 8: Interactive Payment Sandbox (2026-02-07)

### What Was Built
Complete rewrite of `app.py` as a gamified "God Mode" simulator:

### Features
- **Split-Screen Layout**: Payment Terminal (left) + Tribunal War Room (right)
- **Chaos Injector**: Inject 4 failure modes (200 OK, 504 Timeout, 402 Decline, 404 Not Found)
- **Trust Score Slider**: 0.0 (Fraudster) to 1.0 (VIP)
- **Live Agent Debate**: Chat bubbles showing Advocate vs Risk Officer fight
- **Financial Ticker**: Real-time money saved counter
- **Transaction History**: Table with expandable logs per transaction
- **Full Logging**: Each transaction stores settings + agent communications

### Chaos Modes
| Code | Name | Trap |
|------|------|------|
| 200 | Clean Success | No |
| 504 | Gateway Timeout | Yes (Double Spend) |
| 402 | Payment Declined | No |
| 404 | Not Found | Yes (Friendly Fraud) |

### Transaction Log Structure
```python
{
    "timestamp": "HH:MM:SS",
    "tx_id": "TX-XXXXX",
    "user_id": "cust_XXXX",
    "amount": 5000,
    "chaos_mode": "504 GATEWAY TIMEOUT",
    "trust": 0.85,
    "verdict": "ESCALATE",
    "circuit_breaker": True,
    "debate_log": [
        {"agent": "Advocate", "vote": "APPROVE", "msg": "...", "confidence": 85},
        {"agent": "Risk", "vote": "BLOCK", "msg": "...", "confidence": 95},
        {"agent": "Judge", "vote": "ESCALATE", "msg": "...", "confidence": 100}
    ]
}
```

### Run Command
```bash
streamlit run app.py
```

---

## Phase 9: Modular Architecture Refactor (2026-02-07)

### What Was Done
Refactored into 3-file modular architecture:

### Files
| File | Purpose |
|------|---------|
| `core_logic.py` | TribunalBrain class - shared pure Python logic |
| `api.py` | FastAPI middleware with `/v1/process_payment` endpoint |
| `app.py` | Streamlit UI importing TribunalBrain |

### Architecture
```
┌─────────────────┐     ┌─────────────────┐
│   app.py        │────▶│  core_logic.py  │
│  (Streamlit)    │     │  TribunalBrain  │
└─────────────────┘     └────────▲────────┘
                                 │
┌─────────────────┐              │
│    api.py       │──────────────┘
│   (FastAPI)     │
└─────────────────┘
```

### API Endpoint
```bash
POST /v1/process_payment
{
  "amount": 5000,
  "user_trust": 0.9,
  "network_status": "TIMEOUT_504"
}
```

### The Pitch
> "The code running the Simulation is the exact same code
> powering the Live API. One brain, two interfaces."

### Run Commands
```bash
# Terminal 1: API
uvicorn api:app --reload

# Terminal 2: Simulation
streamlit run app.py
```

---

## Phase 10: Complete 4-Component Suite (2026-02-07)

### What Was Built
Expanded from 3-file to full 4-component application suite:

### Components
| File | Purpose | Port |
|------|---------|------|
| `core_logic.py` | TribunalBrain.analyze() - shared decision logic | - |
| `api.py` | FastAPI middleware with POST /webhook | 8000 |
| `dashboard.py` | Ops Console (2 tabs: Simulation + Live Desk) | 8501 |
| `merchant_store.py` | Mock SneakerVault e-commerce store | 8502 |

### Architecture
```
┌─────────────────────┐     ┌─────────────────────┐
│   dashboard.py      │────▶│    core_logic.py    │
│   (Ops Console)     │     │   TribunalBrain     │
└─────────────────────┘     └──────────▲──────────┘
                                       │
┌─────────────────────┐     ┌──────────┴──────────┐
│  merchant_store.py  │────▶│      api.py         │
│   (Mock Store)      │     │   (FastAPI)         │
└─────────────────────┘     └─────────────────────┘
```

### Dashboard Tabs
1. **Simulation Gym**: Direct brain testing (God Mode)
2. **Live Escalation Desk**: Monitor API traffic, highlighted escalations

### Merchant Store Features
- Mock "SneakerVault" UI
- Developer Tools: Simulate bank errors (200/504/402)
- Sends POST /webhook to API
- Displays verdict to customer

### Persistence
- All API transactions saved to `transactions_db.json`
- Dashboard reads from same file for live monitoring

### Run Commands
```bash
# Terminal 1: API
uvicorn api:app --reload

# Terminal 2: Dashboard
streamlit run dashboard.py --server.port 8501

# Terminal 3: Store
streamlit run merchant_store.py --server.port 8502
```

### Demo Flow
1. Open Store (8502) → Buy sneaker with SUCCESS_200 → ✅ Order Confirmed
2. Same store → Developer Tools → TIMEOUT_504 → ⚠️ Payment Under Review
3. Open Dashboard (8501) → Tab 2 → See escalated transaction
4. Pitch: "Same brain, two interfaces, zero losses"
