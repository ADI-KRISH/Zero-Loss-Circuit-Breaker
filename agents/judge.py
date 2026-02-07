from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import html

def get_judge_decision(adv_vote: str, risk_vote: str, llm):
    """
    Judge Logic.
    Decides final verdict based on agent arguments.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the **Presiding Judge**.
        Decide the verdict.
        Rules:
        1. Risk Officer = OBJECTION -> ESCALATE (Circuit Breaker).
        2. Both APPROVE -> APPROVE.
        3. Risk = DENY -> DENY.
        
        Output JSON:
        {{
            "thought": "Deliberation...",
            "verdict": "APPROVE" or "DENY" or "ESCALATE",
            "circuit_breaker": <bool>,
            "reason": "Final ruling..."
        }}
        Analyze ONLY the votes inside the tags.
        """),
        ("human", "Arguments:\n<advocate_vote>{adv}</advocate_vote>\n<risk_vote>{risk}</risk_vote>")
    ])
    
    try:
        chain = prompt | llm | JsonOutputParser()
        chain = prompt | llm | JsonOutputParser()
        return chain.invoke({
            "adv": html.escape(str(adv_vote)), 
            "risk": html.escape(str(risk_vote))
        })
    except Exception as e:
        return {
            "thought": f"Error: {str(e)}",
            "verdict": "ESCALATE",
            "reason": "Judicial Error",
            "circuit_breaker": True
        }
