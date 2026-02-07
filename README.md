# 🛡️ Sentinel: Zero-Loss Circuit Breaker
**AI-Powered Payment Tribunal | Built for EpochOn 2.0 Hackathon**

Sentinel is a multi-agent system that prevents financial loss by detecting ambiguous transaction states (like 504 Timeouts) and triggering a circuit breaker.

---

## 📚 Documentation Index

| File | Description |
| :--- | :--- |
| **[OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md)** | **Start Here!** How to run the 3 terminals and demo scenarios. |
| **[explanation.md](explanation.md)** | Technical Deep-Dive into the LangGraph Architecture (v3.0). |
| **[QA_AUDIT.md](QA_AUDIT.md)** | Security Report detailing the "Red Team" fixes (Race Conditions, Injection). |

---

## 🚀 Quick Start

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set API Key**:
    Create `.env` file with `OPENAI_API_KEY=sk-...`
3.  **Run the System**:
    Follow the steps in **[OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md)**.

---

## 🏗️ Architecture (v3.0)
- **Core Logic**: `core_logic.py` (Orchestrator)
- **Agents**: `agents/advocate.py`, `agents/risk_officer.py`, `agents/judge.py`
- **Frontend**: `dashboard.py` (Streamlit)
- **Store**: `merchant_store.py` (Streamlit)
- **API**: `api.py` (FastAPI)
