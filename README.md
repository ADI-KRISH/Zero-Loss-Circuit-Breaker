# Zero-Loss Circuit Breaker 🛡️

**Autonomous Payment Dispute Resolution Middleware**

> "The most intelligent action in ambiguity is often no action at all."

## What is this?
A multi-agent AI system that resolves payment disputes (Refund vs. Deny). It features a **"Circuit Breaker"** mechanism that strategically refuses to make a decision when data is ambiguous, escalating to humans instead of hallucinating a verdict.

## 🏗️ Architecture

### The Agents (Backend)
- **User Advocate (Blue)**: Argues for the customer.
- **Risk Officer (Red)**: Skeptical, checks for fraud. *Has Veto Power.*
- **Judge (Gold)**: Weighs arguments and signals.
- **Signal Analyst**: Extracts raw facts from Bank API and Ledger.

### The Dashboard (Frontend)
Built with **Streamlit**, offering:
1. **Live Tribunal Simulation**: Watch agents debate in real-time.
2. **Escalation Desk**: Manage cases where the AI "failed safe".

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repo
git clone https://github.com/ADI-KRISH/Zero-Loss-Circuit-Breaker.git
cd Zero-Loss-Circuit-Breaker

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Dashboard (Recommended)
This starts the visual interface.
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

### 3. Run via CLI
If you prefer the terminal:
```bash
python main.py --interactive
```

## 🧪 Test Scenarios

| Scenario | Input Data | Expected Outcome |
|----------|------------|------------------|
| **Happy Path** | Bank: FAILED, Ledger: MISSING | ✅ **REFUND** |
| **Adversarial** | Bank: SUCCESS, Ledger: FOUND | ❌ **DENY** (Fraud detected) |
| **Circuit Breaker** | Bank: TIMEOUT (504) | ⚠️ **ESCALATE** (Safe fallback) |

## 📂 Project Structure
- `app.py`: Streamlit Frontend
- `main.py`: CLI Entry point
- `core/`: Agent logic & LangGraph workflow
- `agents/`: Individual agent prompts/code
- `mock_data/`: Valid and invalid transaction scenarios

## 📖 Documentation
- [Frontend Guide](FRONTEND.md)
- [Development Log](tillnow.md)
