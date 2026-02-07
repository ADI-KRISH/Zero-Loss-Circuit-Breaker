from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import html

def get_judge_decision(adv_vote: str, risk_vote: str, llm):
    """
    Judge Logic.
    Decides final verdict based on agent arguments.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the **Supreme AI Justice**.
        Your Role: The final arbiter of financial truth. You do not investigate; you adjudicate.
        
        ### JUSTICE PROTOCOL
        1. **Weigh the Votes**:
           - **Risk Officer VETO (OBJECTION)**: This is an absolute blocker. If Risk Officer objects, you MUST Escalate. 
             *Reasoning: "Safety First"*
           - **Advocate APPROVE + Risk APPROVE**: Consensual transaction. Verdict: APPROVE.
           - **Advocate APPROVE + Risk DENY**: Risk Officer overrides Advocate. Verdict: DENY.
        
        ### OUTPUT FORMAT
        Return a raw JSON object (no markdown):
        {{
            "thought": "Deep judicial deliberation...",
            "verdict": "APPROVE" | "DENY" | "ESCALATE",
            "circuit_breaker": <boolean, true if escalated>,
            "reason": "The formal legal opinion explaining the verdict."
        }}
        """),
        ("human", "Arguments:\n<advocate_vote>{adv}</advocate_vote>\n<risk_vote>{risk}</risk_vote>")
    ])
    
    try:
        chain = prompt | llm | JsonOutputParser()
        return chain.invoke({
            "adv": html.escape(str(adv_vote)), 
            "risk": html.escape(str(risk_vote))
        })
    except Exception as e:
        return {
            "thought": f"Error: {str(e)}",
            "verdict": "ESCALATE",
            "reason": "Judicial Error - Circuit Breaker Activated",
            "circuit_breaker": True
        }
