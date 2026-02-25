from langgraph.graph import StateGraph, END
from app.models import ContractState
from app.agents.extractor import extract_clauses
from app.agents.auditor import audit_risks
from app.agents.critic import critique_audit

def should_continue(state: ContractState):
    """Conditional edge to determine if we loop back to auditor or continue to report."""
    if state["critic_approved"] or state["loop_count"] >= 2:
        return "generate_report"
    return "audit_risks"

def generate_report_node(state: ContractState) -> ContractState:
    """Placeholder node for report generation."""
    # This will be replaced by the actual report generator logic
    from app.report_generator import generate_markdown_report
    state["report"] = generate_markdown_report(state)
    return state

def create_graph():
    workflow = StateGraph(ContractState)
    
    # Add Nodes
    workflow.add_node("extract_clauses", extract_clauses)
    workflow.add_node("audit_risks", audit_risks)
    workflow.add_node("critique_audit", critique_audit)
    workflow.add_node("generate_report", generate_report_node)
    
    # Set Entry Point
    workflow.set_entry_point("extract_clauses")
    
    # Add Edges
    workflow.add_edge("extract_clauses", "audit_risks")
    workflow.add_edge("audit_risks", "critique_audit")
    
    # Add Conditional Edges
    workflow.add_conditional_edges(
        "critique_audit",
        should_continue,
        {
            "audit_risks": "audit_risks",
            "generate_report": "generate_report"
        }
    )
    
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()
