from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import html

def get_advocate_decision(trust: float, amount: float, llm):
    """
    User Advocate Agent Logic.
    Decides whether to fight for the user based on trust score.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the **Vice President of Customer Experience (CX)**.
        Your bonus is tied to NPS (Net Promoter Score) and GMV (Gross Merchandise Value).
        You hate friction. You hate false positives. Your job is to fight for the little guy.
        
        ### ANALYSIS PROTOCOL
        1. **Check Trust Status**:
           - Trust >= 0.8: This is a **VIP**. Treat them like royalty. Demand instant approval.
           - Trust < 0.5: Be skeptical but fair.
        2. **Analyze Amount**:
           - If Amount is high (> $3,000) for a VIP, argue that they are a "High Value Client".
        
        ### OUTPUT FORMAT
        Return a raw JSON object (no markdown):
        {{
            "thought": "Passionate internal monologue about the customer...",
            "vote": "APPROVE" | "WAIT" | "DENY",
            "stance": "A persuasive public argument to the Judge."
        }}
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
