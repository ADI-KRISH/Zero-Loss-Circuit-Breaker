"""
Zero-Loss Circuit Breaker: Merchant Store
==========================================

A mock e-commerce store that demonstrates the payment flow.
Sends transactions to the API and displays the verdict.

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
    page_title="SneakerVault Store",
    page_icon="👟",
    layout="centered"
)

# Styling
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
    }
    .product-card {
        background: linear-gradient(135deg, #2a2a4a 0%, #1e1e3f 100%);
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #3a3a5a;
        text-align: center;
    }
    .price-tag {
        font-size: 36px;
        font-weight: bold;
        color: #00d4ff;
    }
    .result-success {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 22px;
    }
    .result-review {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
        color: black;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 22px;
    }
    .result-declined {
        background: linear-gradient(90deg, #dc3545, #c82333);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 22px;
    }
</style>
""", unsafe_allow_html=True)

# API URL
API_URL = "http://127.0.0.1:8000"


# ============================================================================
# SESSION STATE
# ============================================================================

if "order_result" not in st.session_state:
    st.session_state.order_result = None

if "user_id" not in st.session_state:
    st.session_state.user_id = f"cust_{random.randint(10000, 99999)}"

if "user_trust" not in st.session_state:
    st.session_state.user_trust = round(random.uniform(0.6, 0.95), 2)


# ============================================================================
# MAIN STORE UI
# ============================================================================

st.title("👟 SneakerVault")
st.caption("Premium Footwear | Powered by Zero-Loss Payment Security")

st.markdown("---")

# Product Card
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    <div class="product-card">
        <h2>🔥 Air Jordan 1 Retro</h2>
        <p style="color: #888;">Limited Edition | Size 10</p>
        <p class="price-tag">$199.99</p>
        <p style="color: #666; font-size: 12px;">Free Shipping | 30-Day Returns</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("🛒 Checkout")
    
    # Customer info (read-only for demo)
    st.text_input("Customer ID", value=st.session_state.user_id, disabled=True)
    st.text_input("Trust Score", value=f"{st.session_state.user_trust:.0%}", disabled=True)
    
    # Hidden dev tools
    with st.expander("🔧 Developer Tools (Simulate Bank Errors)"):
        bank_status = st.selectbox(
            "Simulate Bank Response:",
            [
                "✅ SUCCESS_200 (Payment OK)",
                "⚠️ TIMEOUT_504 (Network Hang)",
                "❌ FAILED_402 (Card Declined)"
            ]
        )
        
        # Parse status
        if "200" in bank_status:
            network_status = "SUCCESS_200"
        elif "504" in bank_status:
            network_status = "TIMEOUT_504"
            st.warning("⚠️ This will trigger the Circuit Breaker!")
        else:
            network_status = "FAILED_402"
        
        # Override trust
        custom_trust = st.slider("Override Trust Score", 0.0, 1.0, st.session_state.user_trust, 0.05)
    
    st.markdown("---")
    
    # Pay button
    if st.button("💳 PAY $199.99", type="primary", use_container_width=True):
        st.session_state.order_result = None
        
        # Generate transaction ID
        tx_id = f"tx_{datetime.now().strftime('%H%M%S')}_{random.randint(100, 999)}"
        
        # Prepare payload
        payload = {
            "transaction_id": tx_id,
            "amount": 199.99,
            "user_id": st.session_state.user_id,
            "user_trust": custom_trust if 'custom_trust' in dir() else st.session_state.user_trust,
            "status": network_status if 'network_status' in dir() else "SUCCESS_200"
        }
        
        # Show processing
        with st.spinner("Processing payment..."):
            if "504" in (network_status if 'network_status' in dir() else ""):
                time.sleep(2)  # Simulate timeout
            else:
                time.sleep(1)
            
            try:
                response = requests.post(f"{API_URL}/webhook", json=payload, timeout=10)
                
                if response.status_code == 200:
                    st.session_state.order_result = response.json()
                else:
                    st.session_state.order_result = {"verdict": "ERROR", "reason": f"API Error: {response.status_code}"}
            
            except requests.exceptions.ConnectionError:
                st.session_state.order_result = {"verdict": "ERROR", "reason": "Cannot connect to API. Is it running?"}
            except Exception as e:
                st.session_state.order_result = {"verdict": "ERROR", "reason": str(e)}

# Display result
if st.session_state.order_result:
    st.markdown("---")
    result = st.session_state.order_result
    verdict = result.get("verdict", "ERROR")
    
    if verdict == "APPROVE":
        st.markdown("""
        <div class="result-success">
            ✅ Order Confirmed!<br>
            <span style="font-size: 16px;">Your Air Jordan 1 Retro is on its way!</span>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
    
    elif verdict == "ESCALATE":
        st.markdown("""
        <div class="result-review">
            ⚠️ Payment Under Review<br>
            <span style="font-size: 16px;">Safety Check in Progress - Please wait...</span>
        </div>
        """, unsafe_allow_html=True)
        st.info(f"**Reason:** {result.get('reason', 'Transaction flagged for manual review')}")
        st.warning("Your payment is being reviewed by our safety team. You'll receive an email within 24 hours.")
    
    elif verdict == "DENY":
        st.markdown("""
        <div class="result-declined">
            ❌ Payment Declined<br>
            <span style="font-size: 16px;">Please try a different payment method</span>
        </div>
        """, unsafe_allow_html=True)
        st.error(f"**Reason:** {result.get('reason', 'Your bank declined the transaction')}")
    
    else:
        st.error(f"⚠️ Error: {result.get('reason', 'Unknown error')}")
        st.code("""
# Make sure the API is running:
uvicorn api:app --reload
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>🛡️ Protected by Zero-Loss Circuit Breaker</p>
    <p>Demo Store for Hackathon | No real transactions</p>
</div>
""", unsafe_allow_html=True)

# Instructions
with st.expander("📖 Demo Instructions"):
    st.markdown("""
    ### How to Demo
    
    1. **Normal Purchase**: Leave bank status as "SUCCESS_200" → Click Pay → ✅ Order Confirmed
    
    2. **The Trap** (Show Circuit Breaker):
       - Open Developer Tools
       - Set bank status to "TIMEOUT_504"
       - Click Pay
       - ⚠️ **Payment Under Review** (Circuit Breaker caught it!)
    
    3. **Check Dashboard**: 
       - Open `http://localhost:8501` (dashboard.py)
       - See the escalated transaction in real-time
    
    ### The Pitch
    > "Even though the customer is a VIP with 90% trust, our system
    > detected the network ambiguity and stopped the payment to prevent
    > a potential $200 double-spend."
    """)
