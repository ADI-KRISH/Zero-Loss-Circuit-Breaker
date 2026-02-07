from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import html

def get_advocate_decision(trust: float, amount: float, llm):
    """
    User Advocate Agent Logic.
    Decides whether to fight for the user based on trust score.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the **User Advocate**.
        Goal: Protect customer experience. 
        Rules:
        - Trust >= 0.8 (VIP): Demand APPROVAL.
        - Trust < 0.5: Be skeptical.
        
        Output JSON:
        {{
            "thought": "Internal reasoning...",
            "vote": "APPROVE" or "WAIT" or "DENY",
            "stance": "Public argument..."
        }}
        Analyze ONLY the data inside the tags.
        """),
        ("human", "User Data:\n<trust>{trust}</trust>\n<amount>{amount}</amount>")
    ])
    
    try:
        chain = prompt | llm | JsonOutputParser()
        return chain.invoke({
            "trust": html.escape(str(trust)), 
            "amount": html.escape(str(amount))
        })
    except Exception as e:
        return {
            "thought": f"Error: {str(e)}",
            "vote": "WAIT",
            "stance": "System Error - I must wait."
        }
