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
