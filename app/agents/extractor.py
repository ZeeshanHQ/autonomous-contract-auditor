import json
from langchain_core.prompts import ChatPromptTemplate
from app.agents.utils import get_llm
from app.models import ContractState

def extract_clauses(state: ContractState) -> ContractState:
    """Agent 1: Extracts specific clauses from the document text."""
    
    llm = get_llm(temperature=0.0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a legal expert specializing in contract extraction. 
        Your task is to identify and extract the following clause types from the provided contract text:
        1. Indemnity
        2. Termination
        3. Governing Law
        4. Limitation of Liability
        5. Intellectual Property
        
        For each clause found, return a JSON object with:
        - "type": The category of the clause.
        - "text": The exact text of the clause.
        - "section": The section number or title if available.
        
        Respond ONLY with a JSON list of these objects. If a clause type is not found, do not include it.
        """),
        ("human", "Contract Text:\n\n{document_text}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({"document_text": state["document_text"]})
    
    # Handle content parsing
    content = response.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        clauses = json.loads(content)
        state["clauses"] = clauses
    except Exception as e:
        print(f"Error parsing clauses: {e}")
        state["clauses"] = []
        
    return state
