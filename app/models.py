from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

# --- LangGraph State Schema ---

class ExtractedClause(TypedDict):
    type: str
    text: str
    section: Optional[str]

class Risk(TypedDict):
    clause_type: str
    risk_level: str  # High, Medium, Low
    issue: str
    toxic_language: Optional[str]
    suggested_alternative: Optional[str]
    recommendation: str

class ContractState(TypedDict):
    # Inputs
    document_text: str
    
    # intermediate outputs
    clauses: List[ExtractedClause]
    risks: List[Risk]
    risk_score: int  # 0-100
    
    # Critic loop state
    critic_approved: bool
    critic_feedback: Optional[str]
    loop_count: int
    
    # Final output
    report: str

# --- API Models ---

class AuditRequest(BaseModel):
    # This might not be needed if we only use file upload,
    # but good to have for direct text audits
    text: Optional[str] = None

class AuditResponse(BaseModel):
    risk_score: int
    report: str
    risks: List[Risk]
    status: str = "completed"
