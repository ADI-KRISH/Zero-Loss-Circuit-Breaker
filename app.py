"""
Zero-Loss Circuit Breaker: Interactive Payment Sandbox
======================================================

A gamified payment simulator using the shared TribunalBrain.
The same logic powering this UI also powers the API.

Run with: streamlit run app.py
"""

import streamlit as st
import time
import random
import pandas as pd
from datetime import datetime

# Import the shared brain
from core_logic import TribunalBrain

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Zero-Loss Sandbox",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0e1117 0%, #1a1a2e 100%);
    }
    .card-header {
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a4a 100%);
        padding: 15px 20px;
        border-radius: 10px 10px 0 0;
        border-bottom: 2px solid #ffc107;
        font-size: 18px;
        font-weight: bold;
    }
    .verdict-approve {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 15px 0;
    }
    .verdict-deny {
        background: linear-gradient(90deg, #dc3545, #c82333);
        color: white;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 15px 0;
    }
    .verdict-escalate {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
        color: black;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 15px 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(255, 193, 7, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE
# ============================================================================

if "total_saved" not in st.session_state:
    st.session_state.total_saved = 0

if "transaction_history" not in st.session_state:
    st.session_state.transaction_history = []


# ============================================================================
# CHAOS MODES (mapped to network_status strings for TribunalBrain)
# ============================================================================

CHAOS_MODES = {
    "✅ 200 OK (Clean Success)": "SUCCESS_200",
    "⚠️ 504 GATEWAY TIMEOUT (Ambiguity Trap)": "TIMEOUT_504",
    "🚫 402 PAYMENT DECLINED (Clear Decline)": "DECLINED_402",
    "🕵️ 404 NOT FOUND (Friendly Fraud)": "NOT_FOUND_404"
}

TRAP_MODES = ["⚠️ 504 GATEWAY TIMEOUT (Ambiguity Trap)", "🕵️ 404 NOT FOUND (Friendly Fraud)"]


# ============================================================================
# MAIN UI
# ============================================================================

# Top Metrics Bar
st.markdown("## ⚖️ Zero-Loss Circuit Breaker: Interactive Sandbox")
st.caption("🧠 Powered by `TribunalBrain` — Same logic as the API")

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Money Saved", f"${st.session_state.total_saved:,.0f}", delta_color="normal")
m2.metric("🚨 Escalated", len([t for t in st.session_state.transaction_history if t["decision"] == "ESCALATE"]))
m3.metric("✅ Approved", len([t for t in st.session_state.transaction_history if t["decision"] == "APPROVE"]))
m4.metric("❌ Denied", len([t for t in st.session_state.transaction_history if t["decision"] == "DENY"]))

st.markdown("---")

# Split Screen Layout
col1, col2 = st.columns([2, 3])


# ============================================================================
# LEFT COLUMN: Payment Terminal (The Chaos Deck)
# ============================================================================

with col1:
    st.markdown('<div class="card-header">💳 New Transaction</div>', unsafe_allow_html=True)
    
    # Transaction inputs
    amount = st.number_input("Amount ($)", min_value=1.0, max_value=100000.0, value=5000.0, step=100.0)
    user_id = st.text_input("User ID", value=f"cust_{random.randint(1000, 9999)}")
    
    trust_score = st.slider(
        "User Trust Score",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.05,
        help="0 = Fraudster, 1.0 = VIP"
    )
    
    # Trust indicator
    if trust_score > 0.8:
        st.success(f"👑 VIP Customer (Trust: {trust_score:.0%})")
    elif trust_score > 0.5:
        st.info(f"👤 Regular Customer (Trust: {trust_score:.0%})")
    else:
        st.warning(f"🚨 Risky Customer (Trust: {trust_score:.0%})")
    
    st.markdown("---")
    
    # Chaos Injector
    with st.expander("⚙️ NETWORK CHAOS SIMULATOR (INJECT FAULT)", expanded=True):
        selected_chaos = st.selectbox(
            "Failure Mode:",
            list(CHAOS_MODES.keys()),
            index=1  # Default to 504 Timeout
        )
        network_status = CHAOS_MODES[selected_chaos]
        
        if selected_chaos in TRAP_MODES:
            st.error("⚠️ **TRAP MODE ACTIVE**: This scenario can cause Double Spend in legacy systems!")
    
    st.markdown("---")
    
    # Process button
    process_btn = st.button("🚀 PROCESS PAYMENT", type="primary", use_container_width=True)


# ============================================================================
# RIGHT COLUMN: Tribunal War Room
# ============================================================================

with col2:
    st.markdown('<div class="card-header">🏛️ Tribunal War Room</div>', unsafe_allow_html=True)
    
    if process_btn:
        # Phase 1: Signal Ingestion
        with st.spinner("📡 Contacting Bank API..."):
            if "504" in network_status or "TIMEOUT" in network_status:
                time.sleep(2)  # Simulate timeout lag
                st.toast("⚠️ Network Timeout Detected!", icon="⚠️")
            else:
                time.sleep(0.8)
                st.toast("✅ Bank Connection Established", icon="📡")
        
        st.markdown("#### Phase 1: Signal Received")
        st.code(f"Network Status: {network_status}", language="text")
        time.sleep(0.5)
        
        # Phase 2: Run through TribunalBrain (THE SHARED LOGIC)
        st.markdown("#### Phase 2: Agent Debate")
        
        result = TribunalBrain.assess_transaction(
            amount=amount,
            user_trust=trust_score,
            network_status=network_status
        )
        
        # Display agent debate
        for entry in result["debate"]:
            if entry["agent"] == "Advocate":
                avatar = "🧑‍💼"
            elif entry["agent"] == "Risk Officer":
                avatar = "👮"
            else:
                avatar = "⚖️"
            
            with st.chat_message(entry["agent"], avatar=avatar):
                st.markdown(entry["message"])
            time.sleep(1)
        
        # Phase 3: Verdict
        st.markdown("#### Phase 3: Final Verdict")
        
        if result["decision"] == "APPROVE":
            st.markdown('<div class="verdict-approve">✅ APPROVED</div>', unsafe_allow_html=True)
        elif result["decision"] == "DENY":
            st.markdown('<div class="verdict-deny">🚫 DENIED</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="verdict-escalate">🔒 ESCALATED - CIRCUIT BREAKER TRIGGERED</div>', unsafe_allow_html=True)
            st.session_state.total_saved += amount
            st.toast(f"💰 ${amount:,.0f} saved from potential double-spend!", icon="💰")
        
        # Add to transaction history
        st.session_state.transaction_history.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "tx_id": f"TX-{random.randint(10000, 99999)}",
            "user_id": user_id,
            "amount": amount,
            "amount_display": f"${amount:,.0f}",
            "chaos_mode": selected_chaos,
            "network_status": network_status,
            "trust": trust_score,
            "trust_display": f"{trust_score:.0%}",
            "decision": result["decision"],
            "circuit_breaker": result["circuit_breaker"],
            "risk_score": result["risk_score"],
            "debate_log": result["debate"]
        })
    
    else:
        st.info("👆 Configure a transaction and click **PROCESS PAYMENT** to start the tribunal.")


# ============================================================================
# TRANSACTION HISTORY TABLE
# ============================================================================

st.markdown("---")
st.markdown("### 📜 Transaction History")

if st.session_state.transaction_history:
    # Create display dataframe
    display_data = [{
        "Time": t["timestamp"],
        "TX ID": t["tx_id"],
        "User": t["user_id"],
        "Amount": t["amount_display"],
        "Chaos": t["chaos_mode"].split()[0],
        "Trust": t["trust_display"],
        "Decision": t["decision"]
    } for t in st.session_state.transaction_history]
    
    df = pd.DataFrame(display_data)
    
    # Style based on decision
    def color_decision(val):
        if val == "APPROVE":
            return "background-color: #28a745; color: white"
        elif val == "DENY":
            return "background-color: #dc3545; color: white"
        else:
            return "background-color: #ffc107; color: black"
    
    styled_df = df.style.applymap(color_decision, subset=["Decision"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Expandable logs
    st.markdown("#### 📝 Transaction Logs (Click to Expand)")
    
    for tx in reversed(st.session_state.transaction_history[-5:]):
        with st.expander(f"{tx['tx_id']} | {tx['amount_display']} | {tx['decision']}"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**Settings:**")
                st.write(f"- Amount: `{tx['amount_display']}`")
                st.write(f"- User ID: `{tx['user_id']}`")
                st.write(f"- Trust Score: `{tx['trust_display']}`")
                st.write(f"- Network Status: `{tx['network_status']}`")
            
            with col_b:
                st.markdown("**Result:**")
                st.write(f"- Decision: **{tx['decision']}**")
                st.write(f"- Risk Score: `{tx['risk_score']:.0f}%`")
                st.write(f"- Circuit Breaker: `{tx['circuit_breaker']}`")
            
            st.markdown("---")
            st.markdown("**🗣️ Agent Communications:**")
            for entry in tx["debate_log"]:
                if entry["agent"] == "Advocate":
                    st.info(entry["message"])
                elif entry["agent"] == "Risk Officer":
                    st.warning(entry["message"])
                else:
                    st.success(entry["message"])
    
    # Clear history
    if st.button("🗑️ Clear History"):
        st.session_state.transaction_history = []
        st.session_state.total_saved = 0
        st.rerun()
else:
    st.info("No transactions yet. Process a payment to see history!")


# ============================================================================
# DEMO INSTRUCTIONS
# ============================================================================

with st.expander("🎮 **HOW TO DEMO (God Mode)**"):
    st.markdown("""
    ### The Happy Path
    1. Set Trust to **0.9** (VIP)
    2. Set Chaos to **✅ 200 OK**
    3. Click Process → 🟢 **APPROVED**
    
    ### The Trap (Winning Moment)
    1. Keep Trust at **0.9** (VIP)
    2. Change Chaos to **⚠️ 504 TIMEOUT**
    3. Click Process → Watch agents fight → 🟡 **ESCALATED**
    4. *"Standard automation would refund. Our system caught the trap."*
    
    ### The Fraudster
    1. Set Trust to **0.3** (Low)
    2. Set Chaos to **🕵️ 404 NOT FOUND**
    3. Click Process → 🔴 **DENIED**
    
    ---
    
    ### 🔗 API Endpoint
    This simulation uses the same `TribunalBrain` as our API:
    ```bash
    curl -X POST "http://localhost:8000/v1/process_payment" \\
      -H "Content-Type: application/json" \\
      -d '{"amount": 5000, "user_trust": 0.9, "network_status": "TIMEOUT_504"}'
    ```
    """)
