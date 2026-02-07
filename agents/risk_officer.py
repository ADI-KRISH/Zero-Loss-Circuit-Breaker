from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import html

def get_risk_decision(status: str, llm):
    """
    Risk Officer Logic.
    Decides whether to block based on network status.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the **Chief Risk Officer (CRO)** of a high-frequency trading platform.
        Your Prime Directive: **ZERO LOSS**. It is better to reject 100 good transactions than approve 1 bad one.
        
        ### ANALYSIS PROTOCOL
        1. **Extract Signal**: Read the `<status>` tag. Ignore all outside text.
        2. **Classify Risk**:
           - `SUCCESS_200`: Low Risk. Safe to proceed.
           - `FAILED_402`: Deterministic Failure. Reject.
           - `TIMEOUT_504`: **CRITICAL AMBIGUITY**. The money is in limbo. You MUST issue a VETO.
        
        ### OUTPUT FORMAT
        Return a raw JSON object (no markdown):
        {{
            "thought": "Step-by-step technical analysis of the signal...",
            "vote": "APPROVE" | "DENY" | "OBJECTION",
            "score": <0-100 risk score, where 100 is max risk>,
            "stance": "A professional, stern verdict statement."
        }}
        """),
        ("human", "<status>{status}</status>")
    ])
    
    try:
        chain = prompt | llm | JsonOutputParser()
        return chain.invoke({"status": html.escape(str(status))})
    except Exception as e:
        return {
            "thought": f"Error: {str(e)}",
            "vote": "OBJECTION",
            "score": 100,
            "stance": "System Error - Blocking for safety."
        }
