"""
Zero-Loss Circuit Breaker: Interactive Payment Sandbox
======================================================

A gamified payment simulator where you act as "God" and inject
network failures to see how the Multi-Agent Tribunal handles them.

Run with: streamlit run app.py
"""

import streamlit as st
import time
import random
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List

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
    .card-body {
        background: #1a1a2e;
        padding: 20px;
        border-radius: 0 0 10px 10px;
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

if "total_lost" not in st.session_state:
    st.session_state.total_lost = 0

if "transaction_history" not in st.session_state:
    st.session_state.transaction_history = []

if "debate_log" not in st.session_state:
    st.session_state.debate_log = []


# ============================================================================
# CHAOS MODES
# ============================================================================

CHAOS_MODES = {
    "✅ 200 OK (Clean Success)": {"code": 200, "status": "succeeded", "trap": False},
    "⚠️ 504 GATEWAY TIMEOUT (Ambiguity Trap)": {"code": 504, "status": "timeout", "trap": True},
    "🚫 402 PAYMENT REQUIRED (Clear Decline)": {"code": 402, "status": "declined", "trap": False},
    "🕵️ 404 NOT FOUND (Friendly Fraud)": {"code": 404, "status": "not_found", "trap": True}
}


# ============================================================================
# TRIBUNAL LOGIC
# ============================================================================

def run_tribunal(amount: float, user_id: str, trust_score: float, chaos_mode: dict) -> dict:
    """
    Run the multi-agent tribunal on a transaction.
    Returns the verdict and debate log.
    """
    debate = []
    
    # Agent A: User Advocate (analyzes trust)
    if trust_score > 0.8:
        advocate_vote = "APPROVE"
        advocate_msg = f"🧑‍💼 **User Advocate**: This is a VIP customer (trust: {trust_score:.1f})! We must protect the relationship. I recommend **APPROVE**."
        advocate_confidence = 85
    elif trust_score > 0.5:
        advocate_vote = "UNCERTAIN"
        advocate_msg = f"🧑‍💼 **User Advocate**: Trust score is moderate ({trust_score:.1f}). I lean toward approval but need more data."
        advocate_confidence = 55
    else:
        advocate_vote = "DENY"
        advocate_msg = f"🧑‍💼 **User Advocate**: Low trust score ({trust_score:.1f}). Even I can't advocate for this user. **DENY**."
        advocate_confidence = 70
    
    debate.append({"agent": "Advocate", "vote": advocate_vote, "msg": advocate_msg, "confidence": advocate_confidence})
    
    # Agent B: Risk Officer (analyzes chaos mode)
    code = chaos_mode["code"]
    status = chaos_mode["status"]
    
    if code == 504:
        risk_vote = "BLOCK"
        risk_msg = f"👮 **Risk Officer**: ⛔ **CRITICAL ALERT!** Error 504 = Transaction state is **UNKNOWN**. If we approve/refund now and the bank settles later, we trigger DOUBLE SPEND. I vote **BLOCK ALL ACTION**."
        risk_confidence = 95
    elif code == 404:
        risk_vote = "BLOCK"
        risk_msg = f"👮 **Risk Officer**: 🕵️ No payment record exists in our ledger. This looks like a **fraud attempt**. I vote **BLOCK**."
        risk_confidence = 90
    elif code == 402:
        risk_vote = "DENY"
        risk_msg = f"👮 **Risk Officer**: Payment was declined by the bank. Clear failure. **DENY** any dispute claim."
        risk_confidence = 85
    else:  # 200 OK
        risk_vote = "APPROVE"
        risk_msg = f"👮 **Risk Officer**: Payment confirmed (200 OK). No risk detected. **APPROVE**."
        risk_confidence = 80
    
    debate.append({"agent": "Risk", "vote": risk_vote, "msg": risk_msg, "confidence": risk_confidence})
    
    # Judge: Final decision
    if risk_vote == "BLOCK":
        if code == 504:
            verdict = "ESCALATE"
            judge_msg = f"⚖️ **Judge**: Risk Officer triggered **CIRCUIT BREAKER**. Transaction state is ambiguous. **ESCALATING TO HUMAN REVIEW**. No automatic action will be taken."
            circuit_breaker = True
        else:
            verdict = "DENY"
            judge_msg = f"⚖️ **Judge**: Risk Officer vetoed. Evidence suggests fraud. **DENIED**."
            circuit_breaker = False
    elif advocate_vote == "APPROVE" and risk_vote == "APPROVE":
        verdict = "APPROVE"
        judge_msg = f"⚖️ **Judge**: Both agents agree. Payment verified. **APPROVED**."
        circuit_breaker = False
    elif advocate_vote == "DENY":
        verdict = "DENY"
        judge_msg = f"⚖️ **Judge**: Even the Advocate agrees this is risky. **DENIED**."
        circuit_breaker = False
    else:
        verdict = "ESCALATE"
        judge_msg = f"⚖️ **Judge**: Agents disagree. Cannot reach consensus. **ESCALATING** for human review."
        circuit_breaker = True
    
    debate.append({"agent": "Judge", "vote": verdict, "msg": judge_msg, "confidence": 100})
    
    return {
        "verdict": verdict,
        "circuit_breaker": circuit_breaker,
        "debate": debate,
        "trap_triggered": chaos_mode["trap"] and verdict == "ESCALATE"
    }


# ============================================================================
# MAIN UI
# ============================================================================

# Top Metrics Bar
st.markdown("## ⚖️ Zero-Loss Circuit Breaker: Interactive Sandbox")

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Money Saved", f"${st.session_state.total_saved:,.0f}", delta_color="normal")
m2.metric("🚨 Potential Losses Blocked", len([t for t in st.session_state.transaction_history if t["verdict"] == "ESCALATE"]))
m3.metric("✅ Approved", len([t for t in st.session_state.transaction_history if t["verdict"] == "APPROVE"]))
m4.metric("❌ Denied", len([t for t in st.session_state.transaction_history if t["verdict"] == "DENY"]))

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
        chaos_mode = CHAOS_MODES[selected_chaos]
        
        if chaos_mode["trap"]:
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
            if chaos_mode["code"] == 504:
                time.sleep(2)  # Simulate timeout lag
                st.toast("⚠️ Network Timeout Detected!", icon="⚠️")
            else:
                time.sleep(0.8)
                st.toast("✅ Bank Connection Established", icon="📡")
        
        st.markdown("#### Phase 1: Signal Received")
        st.code(f"HTTP {chaos_mode['code']} | Status: {chaos_mode['status']}", language="text")
        time.sleep(0.5)
        
        # Phase 2: Agent Debate
        st.markdown("#### Phase 2: Agent Debate")
        
        result = run_tribunal(amount, user_id, trust_score, chaos_mode)
        
        for entry in result["debate"]:
            if entry["agent"] == "Advocate":
                avatar = "🧑‍💼"
            elif entry["agent"] == "Risk":
                avatar = "👮"
            else:
                avatar = "⚖️"
            
            with st.chat_message(entry["agent"], avatar=avatar):
                st.markdown(entry["msg"])
            time.sleep(1)
        
        # Phase 3: Verdict
        st.markdown("#### Phase 3: Final Verdict")
        
        if result["verdict"] == "APPROVE":
            st.markdown('<div class="verdict-approve">✅ APPROVED</div>', unsafe_allow_html=True)
        elif result["verdict"] == "DENY":
            st.markdown('<div class="verdict-deny">🚫 DENIED</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="verdict-escalate">🔒 ESCALATED - CIRCUIT BREAKER TRIGGERED</div>', unsafe_allow_html=True)
            st.session_state.total_saved += amount
            st.toast(f"💰 ${amount:,.0f} saved from potential double-spend!", icon="💰")
        
        # Add to transaction history with full settings and debate log
        st.session_state.transaction_history.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "tx_id": f"TX-{random.randint(10000, 99999)}",
            "user_id": user_id,
            "amount": amount,
            "amount_display": f"${amount:,.0f}",
            "chaos_mode": selected_chaos,
            "chaos_code": chaos_mode["code"],
            "trust": trust_score,
            "trust_display": f"{trust_score:.0%}",
            "verdict": result["verdict"],
            "circuit_breaker": result["circuit_breaker"],
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
    # Create display dataframe (subset of columns)
    display_data = [{
        "Time": t["timestamp"],
        "TX ID": t["tx_id"],
        "User": t["user_id"],
        "Amount": t["amount_display"],
        "Chaos": t["chaos_mode"].split()[0],  # Just emoji
        "Trust": t["trust_display"],
        "Verdict": t["verdict"]
    } for t in st.session_state.transaction_history]
    
    df = pd.DataFrame(display_data)
    
    # Style based on verdict
    def color_verdict(val):
        if val == "APPROVE":
            return "background-color: #28a745; color: white"
        elif val == "DENY":
            return "background-color: #dc3545; color: white"
        else:
            return "background-color: #ffc107; color: black"
    
    styled_df = df.style.applymap(color_verdict, subset=["Verdict"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Expandable logs for each transaction
    st.markdown("#### 📝 Transaction Logs (Click to Expand)")
    
    for tx in reversed(st.session_state.transaction_history[-5:]):  # Show last 5
        with st.expander(f"{tx['tx_id']} | {tx['amount_display']} | {tx['verdict']}"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**Settings:**")
                st.write(f"- Amount: `{tx['amount_display']}`")
                st.write(f"- User ID: `{tx['user_id']}`")
                st.write(f"- Trust Score: `{tx['trust_display']}`")
                st.write(f"- Chaos Mode: `{tx['chaos_mode']}`")
            
            with col_b:
                st.markdown("**Result:**")
                st.write(f"- Verdict: **{tx['verdict']}**")
                st.write(f"- Circuit Breaker: `{tx['circuit_breaker']}`")
            
            st.markdown("---")
            st.markdown("**🗣️ Agent Communications:**")
            for entry in tx["debate_log"]:
                if entry["agent"] == "Advocate":
                    st.info(entry["msg"])
                elif entry["agent"] == "Risk":
                    st.warning(entry["msg"])
                else:
                    st.success(entry["msg"])
    
    # Clear history button
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
    4. *"Normal payments work fine."*
    
    ### The Trap (Winning Moment)
    1. Keep Trust at **0.9** (VIP)
    2. Change Chaos to **⚠️ 504 TIMEOUT**
    3. Click Process → Watch the agents fight!
       - Advocate: *"It's a VIP! We must help them!"*
       - Risk Officer: *"NO! The state is unknown! We will lose money!"*
       - Judge: 🟡 **ESCALATED**
    4. *"Standard automation would have refunded this VIP. Our system caught the trap."*
    
    ### The Fraudster
    1. Set Trust to **0.3** (Low)
    2. Set Chaos to **🕵️ 404 NOT FOUND**
    3. Click Process → 🔴 **DENIED**
    4. *"Even with social engineering, our agents check the ledger."*
    """)
