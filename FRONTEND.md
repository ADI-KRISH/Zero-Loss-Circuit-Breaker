# Zero-Loss Dashboard Guide

## Overview
The **Zero-Loss Dashboard** is the visual interface for the Multi-Agent Tribunal. It allows judges and demo viewers to see the AI agents debate in real-time and demonstrates the "Escalation Desk" workflow for cases that trigger the circuit breaker.

## Features

### 1. Live Simulation Page
- **Scenario Selection**: Choose from 3 pre-built scenarios (Happy Path, Fraud, Circuit Breaker).
- **Run Tribunal**: Trigger the multi-agent debate with a single click.
- **Active Debate View**: Watch as the Advocate (Blue), Risk Officer (Red), and Judge (Gold) discuss the case.
- **Verdict Banner**: Instant visual feedback on the final decision (Green for Refund/Deny, Flashing Yellow for Escalation).

### 2. Escalation Desk Page
- **The "Safe Fallback"**: A queue of all cases where the AI "refused to guess."
- **Deep Dive**: Expand any case to see:
  - The specific reason for escalation (e.g., "Consensus < 60%").
  - Conflicting data points (Bank vs. Ledger).
  - The full chat log of the debate.
- **Human Override**: Buttons to force a REFUND or DENY decision, resolving the ticket.

## How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the App**:
   ```bash
   streamlit run app.py
   ```

3. **Access**:
   The app will open in your browser at `http://localhost:8501`.

## Demo Flow (Winning Pitch)

1. **Start on "Live Simulation"**.
2. Run **Scenario A (Happy Path)** -> Show Green Banner ("Easy refund").
3. Run **Scenario B (Fraud)** -> Show Red Banner ("AI caught the liar").
4. Run **Scenario C (Circuit Breaker)** -> Show **Flashing Yellow Banner** ("AI refused to guess!").
   - *Narrative: "Look! The AI didn't hallucinate a decision. It stopped."*
5. Switch to **"Escalation Desk"**.
   - Show the case pending review.
   - Click "Force Refund".
   - *Narrative: "Humans handle the exceptions. AI handles the scale."*
