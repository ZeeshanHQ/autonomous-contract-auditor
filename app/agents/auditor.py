import json
from langchain_core.prompts import ChatPromptTemplate
from app.agents.utils import get_llm
from app.models import ContractState
from app.config import settings

def audit_risks(state: ContractState) -> ContractState:
    """Agent 2: Audits extracted clauses against risk standards."""
    
    llm = get_llm(temperature=0.1)
    
    # Load risk standards
    try:
        with open(settings.RISK_PLAYBOOK_PATH, "r") as f:
            risk_playbook = json.load(f)
    except Exception as e:
        print(f"Error loading risk playbook: {e}")
        risk_playbook = {"risk_categories": []}
        
    playbook_str = json.dumps(risk_playbook, indent=2)
    clauses_str = json.dumps(state["clauses"], indent=2)
    
    # Check if we have critic feedback (from a loop)
    critic_context = ""
    if state.get("critic_feedback"):
        critic_context = f"\n\nCRITIC FEEDBACK FROM PREVIOUS PASS:\n{state['critic_feedback']}\nPlease address this feedback in your updated audit."

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Contract Lawyer. Your task is to audit the provided contract clauses against a "Risk Playbook".
        
        RISK PLAYBOOK:
        {playbook_str}
        
        TASK:
        For each clause extracted, identify if it contains "Toxic" language, misses required protections, or presents a risk level (High/Medium/Low) based on the playbook.
        
        For each risk found, provide:
        - "clause_type": The category.
        - "risk_level": High, Medium, or Low.
        - "issue": A brief description of the risk.
        - "toxic_language": The specific phrase that is problematic.
        - "suggested_alternative": A legally sound, balanced alternative clause that protects our interest.
        - "recommendation": Actionable advice for the client.
        
        Also, compute an overall "risk_score" from 0-100 (100 being extremely risky).
        
        Respond ONLY with a JSON object:
        {{
            "risks": [{{...}}, {{...}}],
            "risk_score": 85
        }}
        {critic_context}
        """),
        ("human", "Extracted Clauses:\n\n{clauses_str}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "playbook_str": playbook_str,
        "clauses_str": clauses_str,
        "critic_context": critic_context
    })
    
    content = response.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        audit_results = json.loads(content)
        state["risks"] = audit_results.get("risks", [])
        state["risk_score"] = audit_results.get("risk_score", 0)
    except Exception as e:
        print(f"Error parsing audit results: {e}")
        state["risks"] = []
        state["risk_score"] = 0
        
    return state
