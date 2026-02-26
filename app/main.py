import uuid
import asyncio
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from app.pdf_processor import extract_text_from_pdf
from app.agents.graph import create_graph
from app.models import ContractState
import json

app = FastAPI(title="Contract Auditor API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for job status (Simple for production-ready demo)
# For Render free tier, this works within memory limits for single instances
jobs = {}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/audit")
async def start_audit(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    job_id = str(uuid.uuid4())
    content = await file.read()
    
    jobs[job_id] = {
        "status": "QUEUED",
        "progress": 0,
        "message": "Initializing...",
        "result": None
    }
    
    background_tasks.add_task(run_audit_pipeline, job_id, content)
    
    return {"job_id": job_id}

async def run_audit_pipeline(job_id: str, pdf_content: bytes):
    try:
        jobs[job_id].update({"status": "PROCESSING", "progress": 10, "message": "Agent 1: Extracting Clauses..."})
        
        # 1. Extract Text
        text = extract_text_from_pdf(pdf_content)
        if not text:
            jobs[job_id].update({"status": "FAILED", "message": "Failed to extract text from PDF"})
            return
            
        # 2. Run LangGraph with streaming status updates
        graph = create_graph()
        initial_state = {
            "document_text": text,
            "clauses": [],
            "risks": [],
            "risk_score": 0,
            "critic_approved": False,
            "critic_feedback": None,
            "loop_count": 0,
            "report": ""
        }
        
        node_status_map = {
            "extract_clauses": (25, "Agent 1: Clause Context Extracted"),
            "audit_risks": (50, "Agent 2: Audit vs Risk Standards Complete"),
            "critique_audit": (75, "Agent 3: Critic Quality Check Complete"),
            "generate_report": (95, "Finalizing Multimodal Report...")
        }

        final_state = initial_state
        # Run graph in streaming mode to update progress as each node finishes
        for output in graph.stream(initial_state):
            for node_name, state_update in output.items():
                if node_name in node_status_map:
                    progress, message = node_status_map[node_name]
                    # If it's a loop back to audit, customize message
                    if node_name == "audit_risks" and final_state.get("loop_count", 0) > 0:
                        message = f"Agent 2: Re-Auditing (Loop {final_state['loop_count'] + 1})..."
                    
                    jobs[job_id].update({"progress": progress, "message": message})
                    # Update local state so we have the latest for the final report
                    final_state.update(state_update)

        jobs[job_id].update({
            "status": "COMPLETED",
            "progress": 100,
            "message": "Audit Complete!",
            "result": {
                "risk_score": final_state["risk_score"],
                "report": final_state["report"],
                "risks": final_state["risks"]
            }
        })
    except Exception as e:
        print(f"Audit Pipeline Error: {e}")
        jobs[job_id].update({"status": "FAILED", "message": str(e)})

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    async def event_stream():
        last_progress = -1
        last_message = ""
        while True:
            job = jobs.get(job_id)
            if not job:
                break
                
            # Only send if something changed or it's finished
            # CRITICAL FIX: Also check for message changes to keep user engaged
            if job["progress"] != last_progress or job["message"] != last_message or job["status"] in ["COMPLETED", "FAILED"]:
                yield f"data: {json.dumps(job)}\n\n"
                print(f"SSE [{job_id}]: {job['message']} ({job['progress']}%)")
                last_progress = job["progress"]
                last_message = job["message"]
                
            if job["status"] in ["COMPLETED", "FAILED"]:
                break
                
            await asyncio.sleep(0.5) # Poll faster for a more "live" feel
            
    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Serve static frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
