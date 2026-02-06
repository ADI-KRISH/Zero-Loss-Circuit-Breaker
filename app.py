"""
Zero-Loss Circuit Breaker: Dashboard
====================================
Frontend interface for the multi-agent tribunal system.
Run with: streamlit run app.py
"""

import streamlit as st
import time
import pandas as pd
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.schemas import Decision, Verdict, TransactionSignal
from mock_data.scenarios import (
    get_happy_path_scenario,
    get_adversarial_scenario,
    get_circuit_breaker_scenario,
    ALL_SCENARIOS
)
from core.graph import run_tribunal

# Page Configuration
st.set_page_config(
    page_title="Zero-Loss Tribunal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
    .verdict-banner {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 20px;
        color: white;
    }
    .refund-banner {
        background-color: #28a745;
        border: 2px solid #1e7e34;
    }
    .deny-banner {
        background-color: #dc3545;
        border: 2px solid #bd2130;
    }
    .escalate-banner {
        background-color: #ffc107;
        color: #000;
        border: 2px solid #d39e00;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(255, 193, 7, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
    }
    .agent-avatar {
        font-size: 24px;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "escalation_queue" not in st.session_state:
    st.session_state.escalation_queue = []
if "history" not in st.session_state:
    st.session_state.history = []

# --- SCENARIO MAPPING ---
SCENARIOS = {
    "Scenario A: Happy Path (Clear Failure)": get_happy_path_scenario,
    "Scenario B: Fraud Attempt (Clear Success)": get_adversarial_scenario,
    "Scenario C: The Circuit Breaker (Ambiguous 504 Error)": get_circuit_breaker_scenario
}

# --- HELPER FUNCTIONS ---
def display_verdict(verdict: Verdict):
    """Display the final verdict with styling."""
    if verdict.circuit_breaker_triggered:
        st.markdown(f"""
        <div class="verdict-banner escalate-banner">
            ⚠️ CIRCUIT BREAKER TRIGGERED: ESCALATED<br>
            <span style="font-size: 16px; font-weight: normal;">Reason: {verdict.escalation_reason}</span>
        </div>
        """, unsafe_allow_html=True)
        st.error("⚡ STRATEGIC REFUSAL ENGAGED: Workflow Locked. Human Intervention Required.")
    elif verdict.decision == Decision.REFUND:
        st.markdown("""
        <div class="verdict-banner refund-banner">
            💰 VERDICT: REFUND APPROVED
        </div>
        """, unsafe_allow_html=True)
    elif verdict.decision == Decision.DENY:
        st.markdown("""
        <div class="verdict-banner deny-banner">
            🚫 VERDICT: REFUND DENIED
        </div>
        """, unsafe_allow_html=True)

def process_case(case_id, choice):
    """Handle human decision on escalated cases."""
    # Find the case
    for i, case in enumerate(st.session_state.escalation_queue):
        if case['id'] == case_id:
            st.toast(f"Case {case_id} resolved: {choice} issued.")
            # Move to resolved (optional, for now just remove)
            st.session_state.escalation_queue.pop(i)
            st.rerun()
            break

# --- PAGES ---

def page_simulation():
    st.title("🏛️ Tribunal: Live Simulation")
    st.markdown("Run the multi-agent debate system on various payment dispute scenarios.")
    
    # Sidebar
    st.sidebar.header("Configuration")
    selected_scenario_name = st.sidebar.selectbox("Select Test Scenario", list(SCENARIOS.keys()))
    
    # Main Area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("### 📥 Incoming Signal")
        scenario_fn = SCENARIOS[selected_scenario_name]
        signal = scenario_fn()
        
        st.text_input("Transaction ID", signal.transaction_id, disabled=True)
        st.text_input("Amount", f"${signal.amount:.2f}", disabled=True)
        st.text_input("Bank Status", signal.bank_status.value, disabled=True)
        st.text_input("Ledger Status", signal.ledger_status.value, disabled=True)
        st.text_area("User Claim", signal.user_claim, height=100, disabled=True)
        
        run_btn = st.button("⚖️ RUN TRIBUNAL", type="primary")

    with col2:
        st.markdown("### 🗣️ Active Debate")
        chat_container = st.container()
        
        if run_btn:
            with st.spinner("Agents are deliberating..."):
                # Run the backend logic
                try:
                    state = run_tribunal(signal)
                    
                    # Display messages progressively
                    messages = state.get("messages", [])
                    
                    start_time = time.time()
                    
                    # Track rounds to insert headers
                    seen_r1 = False
                    seen_r2 = False
                    seen_r3 = False
                    
                    with chat_container:
                        for sender, msg in messages:
                            # Detect and print Round headers
                            if "Round 1" in msg and not seen_r1:
                                st.markdown("#### 🗣️ Round 1: Opening Statements")
                                st.markdown("---")
                                seen_r1 = True
                                time.sleep(0.5)
                            elif "Round 2" in msg and not seen_r2:
                                st.markdown("#### ⚔️ Round 2: Challenge & Rebuttal")
                                st.markdown("---")
                                seen_r2 = True
                                time.sleep(0.5)
                            elif "Final Vote" in msg and not seen_r3:
                                st.markdown("#### 🗳️ Round 3: Final Votes")
                                st.markdown("---")
                                seen_r3 = True
                                time.sleep(0.5)

                            avatar = "👤"
                            role = "assistant"
                            
                            if "Advocate" in sender:
                                avatar = "🟦" # Blue square/agent
                                sender_name = "User Advocate"
                            elif "Risk" in sender:
                                avatar = "🟥" # Red square/agent
                                sender_name = "Risk Officer"
                            elif "Judge" in sender:
                                avatar = "⚖️" # Scales
                                sender_name = "Judge"
                            elif "Analyst" in sender:
                                avatar = "📊"
                                sender_name = "Signal Analyst"
                            else:
                                sender_name = sender
                            
                            with st.chat_message(sender_name, avatar=avatar):
                                st.write(f"**{sender_name}**: {msg}")
                            
                            # Dynamic sleep based on message length for realism
                            delay = min(0.05 * len(msg.split()), 1.5)
                            time.sleep(delay)
                    
                    # Display Verdict
                    verdict = state.get("verdict")
                    if verdict:
                        display_verdict(verdict)
                        
                        # If Circuit Breaker, add to Escalation Queue
                        if verdict.circuit_breaker_triggered:
                            # Check if already in queue to avoid dupes
                            if not any(c['id'] == signal.transaction_id for c in st.session_state.escalation_queue):
                                st.session_state.escalation_queue.append({
                                    "id": signal.transaction_id,
                                    "amount": signal.amount,
                                    "reason": verdict.escalation_reason,
                                    "timestamp": pd.Timestamp.now(),
                                    "signal": signal,
                                    "verdict": verdict,
                                    "messages": messages
                                })
                                st.sidebar.warning(f"Case {signal.transaction_id} sent to Escalation Desk!")
                
                except Exception as e:
                    st.error(f"Error running tribunal: {e}")
                    # In real app, log error
                    import traceback
                    st.code(traceback.format_exc())

def page_escalation_desk():
    st.title("🚨 Escalation Desk")
    st.markdown("Human review station for cases triggered by the **Zero-Loss Circuit Breaker**.")
    
    queue = st.session_state.escalation_queue
    
    if not queue:
        st.success("🎉 No escalated cases pending review. The system is operating safely.")
        return
    
    st.warning(f"⚠️ {len(queue)} Case(s) Requiring Human Attention")
    
    for case in queue:
        with st.expander(f"Case {case['id']} | ${case['amount']:.2f} | {case['reason']}", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Tribunal Failure Analysis")
                st.markdown(f"**Escalation Reason:** {case['reason']}")
                st.markdown(f"**Confidence:** {case['verdict'].confidence:.1f}% (Below Threshold)")
                
                # Show conflicting data
                st.markdown("#### The Conflicting Signals")
                sig = case['signal']
                data = {
                    "Source": ["Bank API", "Internal Ledger", "User Claim"],
                    "Value": [sig.bank_status.value, sig.ledger_status.value, "Refund Requested"]
                }
                st.table(pd.DataFrame(data))
                
                if st.checkbox(f"Show Full Debate Log for {case['id']}"):
                    for sender, msg in case['messages']:
                         st.text(f"{sender}: {msg}")

                with st.expander("View Raw JSON Data"):
                    st.json(sig.model_dump())
            
            with col2:
                st.subheader("Human override")
                st.markdown("As a human operator, you can force a final decision:")
                
                if st.button("✅ Force REFUND", key=f"ref_{case['id']}", type="primary"):
                    process_case(case['id'], "REFUND")
                
                if st.button("🚫 Force DENY", key=f"deny_{case['id']}", type="secondary"):
                    process_case(case['id'], "DENY")


# --- MAIN APP ROUTING ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Live Simulation", "Escalation Desk"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ System Status")
st.sidebar.success("● AI Agents Online")
st.sidebar.success("● Circuit Breaker Active")

if page == "Live Simulation":
    page_simulation()
elif page == "Escalation Desk":
    page_escalation_desk()

st.sidebar.markdown("---")
st.sidebar.caption("Zero-Loss Circuit Breaker v1.0")
