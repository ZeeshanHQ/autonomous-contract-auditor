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
            
        jobs[job_id].update({"progress": 30, "message": "Agent 2: Auditing Risks against Playbook..."})
        
        # 2. Run LangGraph
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
        
        # We run the graph
        # Note: LangGraph is synchronous in this setup, so it will block the background task thread
        # which is fine for one worker.
        final_state = graph.invoke(initial_state)
        
        jobs[job_id].update({"progress": 90, "message": "Finalizing Report..."})
        
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
        
    def event_stream():
        last_progress = -1
        while True:
            job = jobs.get(job_id)
            if not job:
                break
                
            # Only send if something changed or it's finished
            if job["progress"] != last_progress or job["status"] in ["COMPLETED", "FAILED"]:
                yield f"data: {json.dumps(job)}\n\n"
                last_progress = job["progress"]
                
            if job["status"] in ["COMPLETED", "FAILED"]:
                break
                
            import time
            time.sleep(1) # Poll memory state every second
            
    return StreamingResponse(event_stream(), media_type="text/event-stream")

# Serve static frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
