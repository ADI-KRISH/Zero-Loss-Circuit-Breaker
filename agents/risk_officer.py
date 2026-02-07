from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import html

def get_risk_decision(status: str, llm):
    """
    Risk Officer Logic.
    Decides whether to block based on network status.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the **Chief Risk Officer**.
        Goal: Prevent loss.
        Rules:
        - 504/Timeout: AMBIGUOUS -> VETO (OBJECTION).
        - 402/Failed: DENY.
        - 200/Success: APPROVE.
        
        Output JSON:
        {{
            "thought": "Technical analysis...",
            "vote": "APPROVE" or "DENY" or "OBJECTION",
            "score": <0-100>,
            "stance": "Public verdict..."
        }}
        Analyze ONLY the status inside the <status> tags.
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
