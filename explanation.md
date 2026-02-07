# Sentinel: Zero-Loss Circuit Breaker (Technical Deep-Dive)

**EpochOn 2.0 Hackathon Submission | S4/S6 Multi-Agent Systems**

---

## 📖 Executive Summary
Sentinel is an **AI-Powered Circuit Breaker** for fintech payments. It prevents the classic "Double-Spend" problem caused by network timeouts (504 errors).
Instead of simple if/else logic, it uses a **Multi-Agent Tribunal** (Advocate vs Risk Officer vs Judge) powered by **OpenAI GPT-4o** and orchestrated by **LangGraph**. The system "thinks" about each transaction, and if there is ambiguity, it strategically refuses to decide (Circuit Breaker), saving money.

---

## 🏗️ Technical Architecture (v3.0 - Modular Graph)

The system is built on a **Stateful Graph Architecture** using `LangGraph`.

```mermaid
graph LR
    START -->|Input: Trust & Status| Advocate[Advocate Agent]
    Advocate -->|Vote: APPROVE/WAIT| Risk[Risk Officer Agent]
    Risk -->|Vote: OBJECTION/DENY| Judge[Judge Agent]
    Judge -->|Verdict: ESCALATE| END
```

### 1. The Shared Brain (`core_logic.py`)
This file is the **Orchestrator**. It defines:
- **`TribunalState`**: A TypedDict tracking the transaction lifecycle (Trust, Amount, Votes, Logs).
- **The Graph**: Defines the nodes and edges using `StateGraph`.
- **Deep Logging**: A custom logging system that captures `[THOUGHT]` (internal reasoning) and `[SPEAK]` (public arguments) for every agent.

### 2. The Agent Modules (`agents/` Folder)
The logic for each agent is decoupled into its own module for scalability.
- **`agents/advocate.py`**:
  - **Persona**: Customer Success Manager.
  - **Prompt**: "Protect the VIP user. Trust > 80% = Fight for approval."
  - **Tech**: Uses `ChatPromptTemplate` → `ChatOpenAI` → `JsonOutputParser`.
- **`agents/risk_officer.py`**:
  - **Persona**: Chief Risk Officer.
  - **Prompt**: "If Status is 504 (Timeout), you MUST VETO."
  - **Tech**: Strictly analyzes network codes (`200`, `402`, `504`) using LLM reasoning.
- **`agents/judge.py`**:
  - **Persona**: Supreme Court Justice.
  - **Prompt**: "If Risk Officer objects, TRIGGERS CIRCUIT BREAKER (Escalate)."
  - **Tech**: Synthesizes the two previous arguments into a final JSON verdict.

### 3. The API Layer (`api.py`)
- **Framework**: FastAPI.
- **Role**: Receives POST webhook events from the merchant store.
- **Action**: Instantiates `TribunalBrain`, runs the graph, and saves the full execution trace to `transactions_db.json`.

### 4. The Ops Dashboard (`dashboard.py`)
- **Framework**: Streamlit.
- **Role**: Real-time monitoring for the "Safety Team".
- **Features**:
  - **Live Escalation Desk**: Shows transactions requiring human review.
  - **Internal Monologue**: A "God Mode" view that reveals the *private thoughts* of the AI agents (parsed from the `logs` list).

---

## 🔄 The "Idea to Verdict" Flow

1.  **Trigger**: User buys a $5,000 sneaker on `merchant_store.py`.
2.  **Network Event**: The store simulates a **504 Gateway Timeout** from the bank.
3.  **Graph Execution**:
    *   **Node 1 (Advocate)**: Sees $5,000 + VIP User. *Thought: "I must protect this user."* Vote: **APPROVE**.
    *   **Node 2 (Risk Officer)**: Sees Status 504. *Thought: "Ambiguous state. Money might be lost."* Vote: **OBJECTION**.
    *   **Node 3 (Judge)**: Sees conflict. *Thought: "Risk Officer invoked Veto. I cannot rule."* Verdict: **ESCALATE**.
4.  **Result**: The API returns `ESCALATE` (Circuit Breaker Activated).
5.  **Outcome**: The Store says "Under Review" instead of refunding, preventing a potential $5,000 loss.

---

## 🛡️ Why This Architecture is Better?

1.  **Modular**: Each agent is a separate file. You can upgrade the "Risk Officer" prompt without breaking the "Judge".
2.  **Stateful**: LangGraph manages the state (`TribunalState`) automatically, ensuring no data is lost between agents.
3.  **Dynamic**: There are **zero hardcoded if/else statements** for business logic. All decisions are made by the LLM based on the context.
4.  **Resilient**: The system includes `try/except` blocks to default to "Safety Mode" if the AI service is unreachable.
