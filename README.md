# Zero-Loss Circuit Breaker

> **Multi-Agent Payment Security System** | EpochOn 2.0 Hackathon

An AI-powered payment dispute resolution middleware that uses a Multi-Agent Tribunal to prevent double-spend attacks by strategically refusing to act in ambiguous situations.

---

## 🎯 The Problem

Standard payment automation loses money during network errors:

```
Customer: "My payment failed, give me a refund!"
Legacy Bot: "Error 504? Okay, here's your $5,000 refund!"
Bank (10 seconds later): "Payment actually succeeded."
Result: Customer has goods + refund = DOUBLE SPEND 💸
```

**Our Solution**: An AI Tribunal that **debates** before acting, and **refuses** when uncertain.

---

## 🏗️ Architecture

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

| File | Purpose |
|------|---------|
| `core_logic.py` | TribunalBrain - shared decision logic |
| `api.py` | FastAPI middleware with POST /webhook |
| `dashboard.py` | Ops Console (Simulation + Live Escalation Desk) |
| `merchant_store.py` | Mock e-commerce store for demo |

---

## 🚀 Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the System (3 Terminals)

**Terminal 1: API**
```bash
uvicorn api:app --reload
```

**Terminal 2: Dashboard**
```bash
streamlit run dashboard.py --server.port 8501
```

**Terminal 3: Store**
```bash
streamlit run merchant_store.py --server.port 8502
```

---

## 🎮 Demo Flow

1. **Open Store** → `http://localhost:8502`
2. **Normal Purchase** → SUCCESS_200 → ✅ Order Confirmed
3. **The Trap** → Open Dev Tools → TIMEOUT_504 → ⚠️ Payment Under Review
4. **Show Dashboard** → `http://localhost:8501` → Tab 2 → See escalated transaction

### The Pitch
> *"Even though the customer is a VIP with 90% trust, our system detected the network ambiguity and stopped the payment to prevent a potential $200 double-spend."*

---

## 🧠 The Tribunal Logic

### Agents
| Agent | Role | Decision Factors |
|-------|------|------------------|
| 🧑‍💼 Advocate | Customer-focused | Trust score ≥ 0.8 → APPROVE |
| 👮 Risk Officer | Skeptic (VETO power) | 504 Timeout → BLOCK |
| ⚖️ Judge | Final arbiter | Applies Circuit Breaker |

### Circuit Breaker Triggers
- Advocate votes APPROVE but Risk votes BLOCK → **ESCALATE**
- Network status unknown (504 Timeout) → **ESCALATE**
- No consensus between agents → **ESCALATE**

---

## 📁 Project Structure

```
zero_loss_circuit_breaker/
├── core_logic.py        # 🧠 TribunalBrain (shared logic)
├── api.py               # 🔌 FastAPI middleware
├── dashboard.py         # 📊 Ops Console (Streamlit)
├── merchant_store.py    # 🛒 Mock Store (Streamlit)
├── requirements.txt     # Dependencies
├── transactions_db.json # Auto-generated transaction log
├── README.md            # This file
├── tillnow.md           # Development log
├── core/                # LangGraph implementation (advanced)
├── agents/              # Agent implementations (advanced)
└── models/              # Pydantic schemas
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook` | Process payment transaction |
| GET | `/transactions` | List all transactions |
| GET | `/stats` | Get statistics |
| DELETE | `/transactions` | Clear database |

### Example Request
```bash
curl -X POST "http://localhost:8000/webhook" \
  -H "Content-Type: application/json" \
  -d '{"transaction_id": "tx_001", "amount": 199.99, "user_id": "cust_123", "user_trust": 0.9, "status": "TIMEOUT_504"}'
```

---

## 🔄 Git Recovery

If you need to revert to a previous commit:

```bash
# View commit history
git log --oneline

# Revert to specific commit (safe - creates new commit)
git revert <commit-hash>

# Hard reset (destructive - loses changes)
git reset --hard <commit-hash>
```

---

## 📄 License

MIT License - Built for EpochOn 2.0 Hackathon
