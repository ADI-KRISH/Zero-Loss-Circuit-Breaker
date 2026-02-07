"""
Sentinel: Merchant Store (Sneaker Vault)
=========================================

Mock e-commerce store demonstrating payment flow.
Hidden dev tools allow bank error injection.

HOW TO RUN THE COMPLETE SYSTEM:
================================
Terminal 1: uvicorn api:app --reload
Terminal 2: streamlit run dashboard.py --server.port 8501
Terminal 3: streamlit run merchant_store.py --server.port 8502
"""

import streamlit as st
import requests
import random
import time
from datetime import datetime

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="SneakerVault",
    page_icon="👟",
    layout="centered"
)

# Premium store styling
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%); 
    }
    .store-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
    }
    .product-card {
        background: linear-gradient(135deg, #1e1e3f 0%, #2a2a4a 100%);
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #3a3a5a;
        text-align: center;
    }
    .price-tag {
        font-size: 42px;
        font-weight: bold;
        background: linear-gradient(135deg, #00d4ff, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .result-success {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
    }
    .result-review {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
        color: black;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
        50% { box-shadow: 0 0 20px 10px rgba(255, 193, 7, 0.3); }
    }
    .result-declined {
        background: linear-gradient(135deg, #dc3545, #c82333);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
    }
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000"


# ============================================================================
# SESSION STATE
# ============================================================================

if "order_result" not in st.session_state:
    st.session_state.order_result = None

if "user_id" not in st.session_state:
    st.session_state.user_id = f"cust_{random.randint(10000, 99999)}"

if "user_trust" not in st.session_state:
    st.session_state.user_trust = round(random.uniform(0.75, 0.95), 2)


# ============================================================================
# MAIN STORE UI
# ============================================================================

# Header
st.markdown("""
<div class="store-header">
    <h1 style="margin: 0; color: white;">👟 SneakerVault</h1>
    <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.8);">Premium Footwear | Secured by Sentinel AI</p>
</div>
""", unsafe_allow_html=True)

# Product Display
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    <div class="product-card">
        <h2 style="color: white; margin-top: 0;">🔥 Air Jordan 1 Retro High</h2>
        <p style="color: #888;">Limited Edition | Travis Scott Collab</p>
        <p style="color: #666;">Size: 10 | Condition: DS (Deadstock)</p>
        <p class="price-tag">$4,999</p>
        <p style="color: #666; font-size: 12px; margin-top: 15px;">
            ✓ Authenticity Verified<br>
            ✓ Free Express Shipping<br>
            ✓ 30-Day Returns
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🛒 Secure Checkout")
    
    # Customer Info (simulated)
    st.text_input("👤 Customer ID", value=st.session_state.user_id, disabled=True)
    st.text_input("⭐ Trust Score", value=f"{st.session_state.user_trust:.0%}", disabled=True)
    
    # Card info (fake)
    st.text_input("💳 Card Number", value="•••• •••• •••• 4242", disabled=True)
    
    # Hidden Dev Tools
    st.markdown("---")
    with st.expander("🔧 **Developer Tools** (Force Bank Error)", expanded=False):
        st.caption("Simulate different bank responses for demo purposes")
        
        bank_response = st.selectbox(
            "Bank Response Override:",
            [
                "✅ SUCCESS_200 (Payment OK)",
                "⚠️ TIMEOUT_504 (Network Hang - The Trap!)",
                "❌ FAILED_402 (Card Declined)"
            ],
            index=0
        )
        
        # Parse status
        if "200" in bank_response:
            network_status = "SUCCESS_200"
        elif "504" in bank_response:
            network_status = "TIMEOUT_504"
            st.error("⚠️ This will trigger the Circuit Breaker!")
        else:
            network_status = "FAILED_402"
        
        # Override trust
        override_trust = st.slider(
            "Override Trust Score:",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.user_trust,
            step=0.05
        )
    
    st.markdown("---")
    
    # Pay Button
    if st.button("💳 PAY $4,999", type="primary", use_container_width=True):
        st.session_state.order_result = None
        
        # Generate TX ID
        tx_id = f"TX-{datetime.now().strftime('%H%M%S')}-{random.randint(100, 999)}"
        
        # Prepare payload
        payload = {
            "transaction_id": tx_id,
            "amount": 4999.00,
            "user_id": st.session_state.user_id,
            "user_trust": override_trust if 'override_trust' in dir() else st.session_state.user_trust,
            "status": network_status if 'network_status' in dir() else "SUCCESS_200"
        }
        
        # Show processing
        with st.spinner("🔄 Processing payment through Sentinel..."):
            # Simulate network delay for timeout scenario
            if "504" in (network_status if 'network_status' in dir() else ""):
                time.sleep(2.5)
            else:
                time.sleep(1.2)
            
            try:
                response = requests.post(f"{API_URL}/webhook", json=payload, timeout=15)
                
                if response.status_code == 200:
                    st.session_state.order_result = response.json()
                else:
                    st.session_state.order_result = {
                        "verdict": "ERROR",
                        "reason": f"API returned status {response.status_code}"
                    }
            
            except requests.exceptions.ConnectionError:
                st.session_state.order_result = {
                    "verdict": "ERROR",
                    "reason": "Cannot connect to Sentinel API. Is it running?"
                }
            except Exception as e:
                st.session_state.order_result = {
                    "verdict": "ERROR",
                    "reason": str(e)
                }

# Display Result
if st.session_state.order_result:
    st.markdown("---")
    result = st.session_state.order_result
    verdict = result.get("verdict", "ERROR")
    
    if verdict == "APPROVE":
        st.markdown("""
        <div class="result-success">
            ✅ Order Confirmed!<br>
            <span style="font-size: 16px;">Your Air Jordan 1 Retro is on its way! 🎉</span>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
        st.success(f"**Transaction ID:** {result.get('transaction_id', 'N/A')}")
    
    elif verdict == "ESCALATE":
        st.markdown("""
        <div class="result-review">
            ⚠️ Payment Under Safety Review<br>
            <span style="font-size: 16px;">Our AI detected something unusual. Please wait...</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.warning(f"**Transaction ID:** {result.get('transaction_id', 'N/A')}")
        st.info(f"**Reason:** {result.get('reason', 'Circuit Breaker activated')}")
        
        st.markdown("""
        > 📧 You'll receive an email within 1 hour with the review result.
        > 
        > 🛡️ This safety check protects both you and us from fraud.
        """)
    
    elif verdict == "DENY":
        st.markdown("""
        <div class="result-declined">
            ❌ Payment Declined<br>
            <span style="font-size: 16px;">Please try a different payment method</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.error(f"**Reason:** {result.get('reason', 'Bank declined the transaction')}")
    
    else:
        st.error(f"⚠️ System Error: {result.get('reason', 'Unknown error')}")
        st.code("""
# Make sure the Sentinel API is running:
uvicorn api:app --reload
        """)
    
    # Reset button
    if st.button("🔄 New Order"):
        st.session_state.order_result = None
        st.session_state.user_id = f"cust_{random.randint(10000, 99999)}"
        st.session_state.user_trust = round(random.uniform(0.75, 0.95), 2)
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #555; font-size: 12px;">
    <p>🛡️ Payments secured by <b>Sentinel</b> - Multi-Agent AI Protection</p>
    <p>Demo Store for EpochOn 2.0 Hackathon | No real transactions</p>
</div>
""", unsafe_allow_html=True)

# Demo Instructions
with st.expander("📖 **Demo Instructions**"):
    st.markdown("""
    ### Normal Flow
    1. Click **PAY $4,999** → ✅ Order Confirmed
    
    ### The Trap (Show Circuit Breaker)
    1. Open **Developer Tools**
    2. Set Bank Response to **TIMEOUT_504**
    3. Click **PAY $4,999**
    4. ⚠️ **Payment Under Review** (Circuit Breaker caught it!)
    
    ### Check Dashboard
    1. Open `http://localhost:8501`
    2. Go to **Tab 2: Live Escalation Desk**
    3. Click on the escalated transaction
    4. Show **Internal Monologue** to judges
    
    ### The Pitch
    > *"The customer is a VIP with 90% trust. Traditional automation would approve instantly.*
    > 
    > *But our AI saw the 504 timeout, THOUGHT about the risk, and triggered the Circuit Breaker.*
    > 
    > *That's $5,000 saved from a potential double-spend."*
    """)
