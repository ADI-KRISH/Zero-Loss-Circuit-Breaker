"""
Sentinel: Ops Dashboard
========================

Two-tab dashboard for the Safety Team:
- Tab 1: Simulation Gym with Internal Monologue viewer
- Tab 2: Live Escalation Desk with transaction inspector

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
import random
from datetime import datetime

from core_logic import TribunalBrain

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Sentinel Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Premium styling
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 100%); }
    
    .verdict-approve { 
        background: linear-gradient(135deg, #28a745, #20c997); 
        color: white; padding: 25px; border-radius: 15px; 
        text-align: center; font-size: 28px; font-weight: bold; 
    }
    .verdict-deny { 
        background: linear-gradient(135deg, #dc3545, #c82333); 
        color: white; padding: 25px; border-radius: 15px; 
        text-align: center; font-size: 28px; font-weight: bold; 
    }
    .verdict-escalate { 
        background: linear-gradient(135deg, #ffc107, #fd7e14); 
        color: black; padding: 25px; border-radius: 15px; 
        text-align: center; font-size: 28px; font-weight: bold;
        animation: flash 1s infinite;
    }
    @keyframes flash {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .thought-box {
        background: #1e1e3f;
        border-left: 4px solid #6c757d;
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        color: #aaa;
    }
    .system-box {
        background: #0d1117;
        border-left: 4px solid #58a6ff;
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 0 8px 8px 0;
        color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "transactions_db.json"


# ============================================================================
# HELPER: Display Logs
# ============================================================================

def parse_log(log):
    """Parse log entry - handles both dict and string formats."""
    if isinstance(log, dict):
        return log
    elif isinstance(log, str):
        # Old format: "[TYPE] Agent: message"
        return {"type": "SPEAK", "agent": "System", "message": log}
    return {"type": "UNKNOWN", "agent": "Unknown", "message": str(log)}


def display_logs(logs: list, show_thoughts: bool = True):
    """Display logs with proper formatting."""
    for raw_log in logs:
        log = parse_log(raw_log)
        log_type = log.get("type", "")
        agent = log.get("agent", "")
        message = log.get("message", "")
        
        if log_type == "SYSTEM":
            st.markdown(f'<div class="system-box">🔧 <b>SYSTEM</b>: {message}</div>', unsafe_allow_html=True)
        
        elif log_type == "THOUGHT":
            if show_thoughts:
                st.markdown(f'<div class="thought-box">💭 <b>{agent}</b> (thinking): {message}</div>', unsafe_allow_html=True)
        
        elif log_type == "SPEAK":
            if agent == "Advocate":
                with st.chat_message("Advocate", avatar="🧑‍💼"):
                    st.markdown(message)
            elif agent == "Risk Officer":
                with st.chat_message("Risk Officer", avatar="👮"):
                    st.markdown(message)
            else:
                st.write(message)
        
        elif log_type == "JUDGE":
            with st.chat_message("Judge", avatar="⚖️"):
                st.markdown(f"*{message}*")
        
        elif log_type == "VERDICT":
            with st.chat_message("Judge", avatar="⚖️"):
                st.markdown(f"**{message}**")
        
        else:
            # Unknown format - just display
            st.write(message)


# ============================================================================
# MAIN
# ============================================================================

st.title("🛡️ Sentinel: Multi-Agent Tribunal Dashboard")
st.caption("Transparent AI Decision-Making | Every thought is logged")

tab1, tab2 = st.tabs(["🧪 Simulation Gym", "📊 Live Escalation Desk"])


# ============================================================================
# TAB 1: SIMULATION GYM
# ============================================================================

with tab1:
    st.header("🧪 Simulation Gym (God Mode)")
    st.caption("Test the TribunalBrain directly - see internal thoughts and public debate")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("💳 Transaction Parameters")
        
        tx_id = f"SIM-{random.randint(1000, 9999)}"
        st.text_input("Transaction ID", value=tx_id, disabled=True)
        
        amount = st.number_input("Amount ($)", min_value=1.0, value=4999.00, step=100.0)
        
        trust = st.slider(
            "User Trust Score",
            min_value=0.0,
            max_value=1.0,
            value=0.90,
            step=0.05,
            help="0.0 = Flagged Fraudster | 1.0 = VIP Customer"
        )
        
        # Trust indicator
        if trust >= 0.8:
            st.success(f"👑 VIP Customer ({trust:.0%})")
        elif trust >= 0.5:
            st.info(f"👤 Regular Customer ({trust:.0%})")
        else:
            st.error(f"🚨 Flagged User ({trust:.0%})")
        
        st.markdown("---")
        
        network = st.selectbox(
            "🌐 Network State (Inject Fault)",
            [
                "✅ SUCCESS_200 (Payment Confirmed)",
                "⚠️ TIMEOUT_504 (The Trap!)",
                "❌ FAILED_402 (Bank Declined)"
            ]
        )
        
        # Parse status
        if "200" in network:
            status = "SUCCESS_200"
        elif "504" in network:
            status = "TIMEOUT_504"
            st.error("⚠️ **TRAP MODE ACTIVE**: This triggers Circuit Breaker!")
        else:
            status = "FAILED_402"
        
        st.markdown("---")
        
        run_btn = st.button("🚀 RUN TRIBUNAL", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("🏛️ Tribunal Deliberation")
        
        if run_btn:
            with st.spinner("Activating Multi-Agent Tribunal..."):
                time.sleep(0.5)
                result = TribunalBrain.analyze(tx_id, amount, trust, status)
            
            # Verdict Banner
            verdict = result["verdict"]
            if verdict == "APPROVE":
                st.markdown(f'<div class="verdict-approve">✅ APPROVED</div>', unsafe_allow_html=True)
            elif verdict == "DENY":
                st.markdown(f'<div class="verdict-deny">❌ DENIED</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="verdict-escalate">🔒 ESCALATED - CIRCUIT BREAKER</div>', unsafe_allow_html=True)
            
            st.info(f"**Reason:** {result['reason']}")
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Advocate", result["advocate_vote"])
            m2.metric("Risk Officer", result["risk_vote"])
            m3.metric("Risk Score", f"{result['risk_score']:.0f}%")
            
            st.markdown("---")
            
            # Internal Monologue (The "Wow" Factor)
            with st.expander("🧠 **Show Internal Monologue** (Agent Thoughts)", expanded=True):
                st.caption("These are the private thoughts of each agent - not visible to other agents during debate")
                thoughts = [l for l in result["logs"] if l["type"] == "THOUGHT"]
                for t in thoughts:
                    st.markdown(f'<div class="thought-box">💭 <b>{t["agent"]}</b>: {t["message"]}</div>', unsafe_allow_html=True)
            
            # Full Debate (Public Statements)
            st.subheader("🗣️ Public Debate")
            display_logs(result["logs"], show_thoughts=False)
        
        else:
            st.info("👈 Configure parameters and click **RUN TRIBUNAL** to see the agents debate")


# ============================================================================
# TAB 2: LIVE ESCALATION DESK
# ============================================================================

with tab2:
    st.header("📊 Live Escalation Desk")
    st.caption("Monitor real-time API traffic from the Merchant Store")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Load database
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
        money_saved = sum(t.get("amount", 0) for t in transactions if t.get("circuit_breaker", False))
        
        m1.metric("Total Transactions", total)
        m2.metric("✅ Approved", approved)
        m3.metric("🔒 Escalated", escalated)
        m4.metric("💰 Money Saved", f"${money_saved:,.2f}")
        
        st.markdown("---")
        
        # Transaction Table
        st.subheader("📋 Recent Transactions")
        
        display_data = [{
            "Time": t.get("timestamp", "")[:19],
            "TX ID": t.get("transaction_id", ""),
            "User": t.get("user_id", ""),
            "Amount": f"${t.get('amount', 0):,.2f}",
            "Trust": f"{t.get('user_trust', 0):.0%}",
            "Network": t.get("network_status", ""),
            "Advocate": t.get("advocate_vote", ""),
            "Risk": t.get("risk_vote", ""),
            "Verdict": t.get("verdict", "")
        } for t in reversed(transactions)]
        
        df = pd.DataFrame(display_data)
        
        def highlight_verdict(row):
            v = row["Verdict"]
            if v == "ESCALATE":
                return ["background-color: #ffc107; color: black"] * len(row)
            elif v == "DENY":
                return ["background-color: #dc3545; color: white"] * len(row)
            elif v == "APPROVE":
                return ["background-color: #28a745; color: white"] * len(row)
            return [""] * len(row)
        
        styled_df = df.style.apply(highlight_verdict, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Transaction Inspector
        st.markdown("---")
        st.subheader("🔍 Transaction Inspector")
        
        tx_ids = [t.get("transaction_id") for t in reversed(transactions)]
        selected_tx = st.selectbox("Select Transaction to Inspect", tx_ids)
        
        if selected_tx:
            tx = next((t for t in transactions if t.get("transaction_id") == selected_tx), None)
            if tx:
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("**Transaction Details:**")
                    st.write(f"- Amount: `${tx.get('amount', 0):,.2f}`")
                    st.write(f"- User: `{tx.get('user_id')}`")
                    st.write(f"- Trust: `{tx.get('user_trust', 0):.0%}`")
                    st.write(f"- Network: `{tx.get('network_status')}`")
                
                with col_b:
                    st.markdown("**Verdict:**")
                    st.write(f"- Decision: **{tx.get('verdict')}**")
                    st.write(f"- Risk Score: `{tx.get('risk_score', 0):.0f}%`")
                    st.write(f"- Circuit Breaker: `{tx.get('circuit_breaker')}`")
                    st.write(f"- Reason: {tx.get('reason')}")
                
                st.markdown("---")
                
                with st.expander("🧠 **Internal Monologue**", expanded=False):
                    raw_logs = tx.get("logs", [])
                    thoughts = [parse_log(l) for l in raw_logs if parse_log(l).get("type") == "THOUGHT"]
                    if thoughts:
                        for t in thoughts:
                            st.markdown(f'<div class="thought-box">💭 <b>{t.get("agent", "Agent")}</b>: {t.get("message", "")}</div>', unsafe_allow_html=True)
                    else:
                        st.info("No internal thoughts recorded for this transaction (old format).")
                
                st.markdown("**Full Debate Log:**")
                display_logs(tx.get("logs", []), show_thoughts=False)
        
        # Clear button
        st.markdown("---")
        if st.button("🗑️ Clear All Transactions"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.success("Database cleared!")
            st.rerun()
    
    else:
        st.info("📭 No transactions yet. Start the Merchant Store to generate traffic!")
        st.code("""
# Start the API:
uvicorn api:app --reload

# Start the Merchant Store:
streamlit run merchant_store.py --server.port 8502
        """)


# ============================================================================
# DEMO GUIDE
# ============================================================================

with st.expander("💡 **How to Present to Judges**"):
    st.markdown("""
    ### The Demo Flow
    
    1. **Open Tab 1 (Simulation Gym)**
    2. Set Trust to **0.90** (VIP) and Network to **TIMEOUT_504**
    3. Click **RUN TRIBUNAL**
    4. **Expand "Internal Monologue"**
    
    ### The Pitch
    
    > *"Standard AI is a black box. Our system is transparent.*
    > 
    > *Look here—you can see Agent B THINKING about the risk before it even speaks.*
    > 
    > *You can see the exact moment the logic switched from 'Trust User' to 'Protect Asset'.*
    > 
    > *This is the Visible Disagreement that prevents financial loss."*
    
    ### What to Highlight
    
    - **THOUGHT logs**: Show agents reasoning privately
    - **SPEAK logs**: Show public debate
    - **Circuit Breaker**: Yellow banner = money saved
    """)
