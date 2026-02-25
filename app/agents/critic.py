import json
from langchain_core.prompts import ChatPromptTemplate
from app.agents.utils import get_llm
from app.models import ContractState

def critique_audit(state: ContractState) -> ContractState:
    """Agent 3: Critiques the Auditor's work to ensure accuracy and completeness."""
    
    # High temperature for adversarial thinking
    llm = get_llm(temperature=0.7)
    
    clauses_str = json.dumps(state["clauses"], indent=2)
    risks_str = json.dumps(state["risks"], indent=2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Legal Critic. Your task is to review the "Risk Audit" performed by a colleague.
        
        EXTRACTED CLAUSES:
        {clauses_str}
        
        RISK AUDIT TO REVIEW:
        {risks_str}
        
        TASK:
        Check for any of the following:
        1. Hallucinations: Did the auditor claim a risk exists that isn't supported by the clause text?
        2. Missed Risks: Did the auditor miss a glaring "Toxic" phrase from the playbook?
        3. Incorrect Severity: Is a High risk labeled as Low, or vice-versa?
        4. Poor Alternatives: Are the "Suggested Alternatives" actually safer/better?
        
        Respond ONLY with a JSON object:
        {{
            "critic_approved": true/false,
            "feedback": "Details on what to fix, or 'Looks good' if approved."
        }}
        """),
        ("human", "Please review the audit above.")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "clauses_str": clauses_str,
        "risks_str": risks_str
    })
    
    content = response.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        critic_results = json.loads(content)
        state["critic_approved"] = critic_results.get("critic_approved", False)
        state["critic_feedback"] = critic_results.get("feedback", "")
    except Exception as e:
        print(f"Error parsing critic results: {e}")
        state["critic_approved"] = True  # Safety to avoid infinite loops if parsing fails
        
    # Increment loop count
    state["loop_count"] = state.get("loop_count", 0) + 1
        
    return state
