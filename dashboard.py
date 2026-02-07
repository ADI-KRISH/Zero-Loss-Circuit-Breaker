"""
Zero-Loss Circuit Breaker: Ops Dashboard
=========================================

A Streamlit dashboard for the Safety Team with:
- Tab 1: Simulation Gym (test the Brain directly)
- Tab 2: Live Escalation Desk (monitor API traffic)

HOW TO RUN THE COMPLETE SYSTEM:
================================
Terminal 1: uvicorn api:app --reload
Terminal 2: streamlit run dashboard.py --server.port 8501
Terminal 3: streamlit run merchant_store.py --server.port 8502
"""

import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime

from core_logic import TribunalBrain

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Zero-Loss Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Styling
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0e1117 0%, #1a1a2e 100%); }
    .verdict-approve { background: #28a745; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; }
    .verdict-deny { background: #dc3545; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; }
    .verdict-escalate { background: #ffc107; color: black; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Database file (shared with api.py)
DB_FILE = "transactions_db.json"


# ============================================================================
# SESSION STATE
# ============================================================================

if "sim_history" not in st.session_state:
    st.session_state.sim_history = []


# ============================================================================
# MAIN
# ============================================================================

st.title("🛡️ Zero-Loss Circuit Breaker: Ops Dashboard")
st.caption("Safety Team Console | Powered by TribunalBrain")

tab1, tab2 = st.tabs(["🧪 Simulation Gym", "📊 Live Escalation Desk"])


# ============================================================================
# TAB 1: SIMULATION GYM (Direct Brain Testing)
# ============================================================================

with tab1:
    st.header("🧪 Simulation Gym")
    st.caption("Test the TribunalBrain directly without hitting the API")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("💳 Inject Transaction")
        
        amount = st.number_input("Amount ($)", min_value=1.0, value=199.99, step=10.0)
        
        trust = st.slider(
            "User Trust Score",
            min_value=0.0,
            max_value=1.0,
            value=0.85,
            step=0.05,
            help="0 = Fraudster, 1.0 = VIP"
        )
        
        # Trust indicator
        if trust >= 0.8:
            st.success(f"👑 VIP Customer ({trust:.0%})")
        elif trust >= 0.5:
            st.info(f"👤 Regular Customer ({trust:.0%})")
        else:
            st.warning(f"🚨 Risky Customer ({trust:.0%})")
        
        network_status = st.selectbox(
            "Network Fault Injection",
            [
                "SUCCESS_200 (Clean)",
                "TIMEOUT_504 (The Trap!)",
                "FAILED_402 (Declined)"
            ]
        )
        
        # Extract status code
        if "200" in network_status:
            status = "SUCCESS_200"
        elif "504" in network_status:
            status = "TIMEOUT_504"
        else:
            status = "FAILED_402"
        
        if "504" in network_status:
            st.error("⚠️ **TRAP MODE**: This simulates an ambiguous network state!")
        
        inject_btn = st.button("🚀 INJECT TRANSACTION", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("🏛️ Tribunal Response")
        
        if inject_btn:
            # Run through brain
            with st.spinner("Analyzing transaction..."):
                time.sleep(0.5)
                result = TribunalBrain.analyze(amount, trust, status)
            
            # Display agent chat logs
            st.markdown("#### 🗣️ Agent Debate")
            for log in result["logs"]:
                if "Advocate" in log:
                    with st.chat_message("Advocate", avatar="🧑‍💼"):
                        st.markdown(log.replace("🧑‍💼 **Advocate**: ", ""))
                elif "Risk Officer" in log:
                    with st.chat_message("Risk Officer", avatar="👮"):
                        st.markdown(log.replace("👮 **Risk Officer**: ", ""))
                else:
                    with st.chat_message("Judge", avatar="⚖️"):
                        st.markdown(log.replace("⚖️ **Judge**: ", ""))
                time.sleep(0.3)
            
            # Verdict banner
            st.markdown("---")
            verdict = result["verdict"]
            if verdict == "APPROVE":
                st.markdown(f'<div class="verdict-approve">✅ {verdict}</div>', unsafe_allow_html=True)
            elif verdict == "DENY":
                st.markdown(f'<div class="verdict-deny">❌ {verdict}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="verdict-escalate">🔒 {verdict} - CIRCUIT BREAKER</div>', unsafe_allow_html=True)
            
            st.info(f"**Reason:** {result['reason']}")
            
            # Add to history
            st.session_state.sim_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "amount": f"${amount:,.2f}",
                "trust": f"{trust:.0%}",
                "status": status,
                "verdict": verdict
            })
        else:
            st.info("👆 Configure a transaction and click **INJECT** to test the Brain")
    
    # Simulation history
    if st.session_state.sim_history:
        st.markdown("---")
        st.subheader("📜 Simulation History")
        df = pd.DataFrame(st.session_state.sim_history)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Clear History"):
            st.session_state.sim_history = []
            st.rerun()


# ============================================================================
# TAB 2: LIVE ESCALATION DESK (Monitor API Traffic)
# ============================================================================

with tab2:
    st.header("📊 Live Escalation Desk")
    st.caption("Monitor real-time API traffic from the Merchant Store")
    
    # Refresh button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("🔄 Refresh Feed", use_container_width=True):
            st.rerun()
    
    # Load transactions from database
    transactions = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                transactions = json.load(f)
        except:
            transactions = []
    
    if transactions:
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        
        total = len(transactions)
        approved = sum(1 for t in transactions if t.get("verdict") == "APPROVE")
        denied = sum(1 for t in transactions if t.get("verdict") == "DENY")
        escalated = sum(1 for t in transactions if t.get("verdict") == "ESCALATE")
        money_saved = sum(t.get("amount", 0) for t in transactions if t.get("verdict") in ["ESCALATE", "DENY"])
        
        m1.metric("Total Transactions", total)
        m2.metric("✅ Approved", approved)
        m3.metric("🔒 Escalated", escalated)
        m4.metric("💰 Money Saved", f"${money_saved:,.2f}")
        
        st.markdown("---")
        
        # Transaction table
        st.subheader("📋 Transaction Feed")
        
        display_data = [{
            "Time": t.get("timestamp", "")[:19],
            "TX ID": t.get("transaction_id", ""),
            "User": t.get("user_id", ""),
            "Amount": f"${t.get('amount', 0):,.2f}",
            "Trust": f"{t.get('user_trust', 0):.0%}",
            "Network": t.get("network_status", ""),
            "Verdict": t.get("verdict", ""),
            "Risk": f"{t.get('risk_score', 0):.0f}%"
        } for t in reversed(transactions)]
        
        df = pd.DataFrame(display_data)
        
        # Highlight escalated rows
        def highlight_verdict(row):
            if row["Verdict"] == "ESCALATE":
                return ["background-color: #ffc107; color: black"] * len(row)
            elif row["Verdict"] == "DENY":
                return ["background-color: #dc3545; color: white"] * len(row)
            elif row["Verdict"] == "APPROVE":
                return ["background-color: #28a745; color: white"] * len(row)
            return [""] * len(row)
        
        styled_df = df.style.apply(highlight_verdict, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Escalation details
        escalated_txs = [t for t in transactions if t.get("verdict") == "ESCALATE"]
        if escalated_txs:
            st.markdown("---")
            st.subheader("🚨 Escalated Transactions (Pending Human Review)")
            
            for tx in reversed(escalated_txs[-5:]):
                with st.expander(f"🔒 {tx.get('transaction_id')} - ${tx.get('amount', 0):,.2f}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**User:** {tx.get('user_id')}")
                        st.write(f"**Trust:** {tx.get('user_trust', 0):.0%}")
                        st.write(f"**Network:** `{tx.get('network_status')}`")
                    with col_b:
                        st.write(f"**Risk Score:** {tx.get('risk_score', 0):.0f}%")
                        st.write(f"**Reason:** {tx.get('reason')}")
                    
                    st.markdown("**Agent Logs:**")
                    for log in tx.get("logs", []):
                        st.write(log)
        
        # Clear button
        st.markdown("---")
        if st.button("🗑️ Clear All Transactions"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.success("Database cleared!")
            st.rerun()
    
    else:
        st.info("📭 No transactions yet. Run the Merchant Store to generate traffic!")
        st.code("""
# Start the API in Terminal 1:
uvicorn api:app --reload

# Start the Merchant Store in Terminal 3:
streamlit run merchant_store.py --server.port 8502
        """)
