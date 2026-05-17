"""
EHS AI POC - FastAPI Backend
Main API server orchestrating CV, reasoning, knowledge base, and report generation.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("ehs_api")

# ─── App Setup ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="EHS AI POC API",
    description="Agentic AI for Environment Health & Safety Monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Module Initialization ────────────────────────────────────────────────────
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", str(BASE_DIR / "reports")))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_BASE_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", str(BASE_DIR / "knowledge_base")))
CHROMA_DB_DIR = str(Path(os.getenv("CHROMA_DB_DIR", str(BASE_DIR / "data" / "chroma_db"))))

# Lazy-loaded modules
_cv_detector = None
_knowledge_base = None
_reasoning_agent = None


def get_cv_detector():
    global _cv_detector
    if _cv_detector is None:
        from cv_module import SafetyDetector

        confidence = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))

        # IMPORTANT: correct model paths
        person_model = os.getenv("PERSON_MODEL_PATH", str(BASE_DIR / "models" / "yolov8s.pt"))
        ppe_model = os.getenv("PPE_MODEL_PATH", str(BASE_DIR / "models" / "ppe_detection.pt"))

        _cv_detector = SafetyDetector(
            person_model_path=person_model,
            ppe_model_path=ppe_model,
            confidence=confidence
        )

    return _cv_detector


def get_knowledge_base():
    global _knowledge_base
    if _knowledge_base is None:
        from knowledge_base_module import EHSKnowledgeBase
        policies_path = str(KNOWLEDGE_BASE_DIR / "ehs_policies.json")
        _knowledge_base = EHSKnowledgeBase(
            persist_dir=CHROMA_DB_DIR,
            policies_path=policies_path
        )
    return _knowledge_base


def get_reasoning_agent():
    global _reasoning_agent
    if _reasoning_agent is None:
        from reasoning_agent import EHSReasoningAgent
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        _reasoning_agent = EHSReasoningAgent(model=model)
    return _reasoning_agent


# ─── Request/Response Models ──────────────────────────────────────────────────

class PolicyQueryRequest(BaseModel):
    question: str
    category_filter: Optional[str] = None
    n_results: int = 4


class AnalyzeImageRequest(BaseModel):
    image_base64: str  # base64 encoded image
    location: str = "Industrial Floor A"
    generate_report: bool = True


class IncidentReportRequest(BaseModel):
    assessment: dict
    cv_results: dict
    policy_context: str
    location: str = "Industrial Floor A"


# ─── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "EHS AI POC",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "analyze_image": "POST /analyze/image",
            "analyze_upload": "POST /analyze/upload",
            "query_policy": "POST /knowledge/query",
            "list_categories": "GET /knowledge/categories",
            "list_reports": "GET /reports",
            "get_report": "GET /reports/{report_id}",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Check status of all system components."""
    status = {
        "api": "healthy",
        "timestamp": datetime.now().isoformat()
    }

    # Check Groq API
    groq_key = os.getenv("GROQ_API_KEY", "")
    status["groq_api"] = "configured" if groq_key and groq_key != "your_groq_api_key_here" else "not_configured"

    # Check KB
    try:
        kb = get_knowledge_base()
        stats = kb.get_stats()
        status["knowledge_base"] = {
            "status": "healthy" if stats.get("initialized") else "degraded",
            "policies": stats.get("total_policies", 0),
            "chunks": stats.get("total_chunks", 0)
        }
    except Exception as e:
        status["knowledge_base"] = {"status": "error", "error": str(e)}

    # Check CV
    try:
        detector = get_cv_detector()
        status["cv_module"] = {
            "status": "healthy",
            "model": "yolov8n" if detector.model else "heuristic_fallback"
        }
    except Exception as e:
        status["cv_module"] = {"status": "error", "error": str(e)}

    status["reports_dir"] = str(REPORTS_DIR)
    status["reports_count"] = len(list(REPORTS_DIR.glob("*.json")))

    return status


@app.post("/analyze/image")
async def analyze_image_base64(request: AnalyzeImageRequest):
    """
    Full EHS analysis pipeline:
    1. CV detection on base64 image
    2. Policy retrieval from KB
    3. Agentic compliance assessment
    4. Incident report generation (if violations found)
    """
    try:
        # Step 1: Computer Vision
        logger.info("Step 1: Running CV analysis...")
        detector = get_cv_detector()
        cv_results = detector.process_image(request.image_base64)

        # Step 2: Knowledge Base Retrieval
        logger.info("Step 2: Querying knowledge base...")
        kb = get_knowledge_base()

        # Build smart query from CV findings
        query_parts = []
        if cv_results["summary"]["ppe_violations"] > 0:
            query_parts.append("PPE personal protective equipment requirements")
        for hazard in cv_results["hazards_detected"]:
            query_parts.append(hazard["type"].replace("_", " "))
        query_parts.append("safety compliance industrial floor")

        query = " ".join(query_parts) if query_parts else "general workplace safety requirements"
        kb_results = kb.query(query, n_results=5)

        policy_context = "\n\n".join([
            f"[{r['policy_id']} - {r['title']}]\n{r['content']}"
            for r in kb_results["results"]
        ])

        # Step 3: Agentic Reasoning
        logger.info("Step 3: Running compliance assessment...")
        agent = get_reasoning_agent()
        assessment = agent.assess_compliance(cv_results, policy_context)

        # Step 4: Generate Report (if violations or user requested)
        report = None
        report_id = None
        if request.generate_report and (
            assessment.get("overall_compliance_status") in ["VIOLATION", "WARNING"]
            or cv_results["summary"]["requires_review"]
        ):
            logger.info("Step 4: Generating incident report...")
            report = agent.generate_incident_report(
                assessment, cv_results, policy_context, request.location
            )
            report_id = report.get("report_id", f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}")

            # Persist report
            report_path = REPORTS_DIR / f"{report_id}.json"
            full_report = {
                **report,
                "cv_results_summary": cv_results["summary"],
                "assessment": {k: v for k, v in assessment.items() if k != "raw_llm_response"},
                "kb_policies_used": [r["policy_id"] for r in kb_results["results"]],
                "annotated_image": cv_results.get("annotated_image")
            }
            with open(report_path, "w") as f:
                json.dump(full_report, f, indent=2, default=str)
            logger.info(f"Report saved: {report_path}")

        return {
            "status": "success",
            "pipeline_steps_completed": 4 if report else 3,
            "cv_results": {
                "summary": cv_results["summary"],
                "detections": cv_results["detections"],
                "ppe_analysis": cv_results["ppe_analysis"],
                "hazards": cv_results["hazards_detected"],
                "annotated_image": cv_results.get("annotated_image"),
                "image_dimensions": cv_results["image_dimensions"]
            },
            "policies_retrieved": kb_results["results"][:3],
            "assessment": {k: v for k, v in assessment.items() if k != "raw_llm_response"},
            "incident_report": report,
            "report_id": report_id,
            "report_saved": report is not None
        }

    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/upload")
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    location: str = "Industrial Floor A",
    generate_report: bool = True
):
    """Upload image file for EHS analysis."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    import base64
    contents = await file.read()
    image_b64 = base64.b64encode(contents).decode("utf-8")

    req = AnalyzeImageRequest(
        image_base64=image_b64,
        location=location,
        generate_report=generate_report
    )
    return await analyze_image_base64(req)


@app.post("/knowledge/query")
async def query_knowledge_base(request: PolicyQueryRequest):
    """Query EHS policy knowledge base with semantic search."""
    try:
        kb = get_knowledge_base()
        results = kb.query(
            question=request.question,
            n_results=request.n_results,
            category_filter=request.category_filter
        )

        # Also get AI-powered answer
        if results["results"]:
            agent = get_reasoning_agent()
            policy_context = "\n\n".join([
                f"[{r['policy_id']} - {r['title']}]\n{r['content']}"
                for r in results["results"]
            ])
            ai_answer = agent.answer_policy_question(request.question, policy_context)
        else:
            ai_answer = "No relevant policies found for your query."

        return {
            "question": request.question,
            "ai_answer": ai_answer,
            "retrieved_policies": results["results"],
            "total_results": results["total_results"]
        }
    except Exception as e:
        logger.error(f"KB query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge/categories")
async def list_categories():
    """List all EHS policy categories in knowledge base."""
    kb = get_knowledge_base()
    return {"categories": kb.get_all_categories()}


@app.get("/knowledge/stats")
async def kb_stats():
    """Get knowledge base statistics."""
    kb = get_knowledge_base()
    return kb.get_stats()


@app.get("/reports")
async def list_reports():
    """List all generated incident reports."""
    reports = []
    for report_file in sorted(REPORTS_DIR.glob("*.json"), reverse=True):
        try:
            with open(report_file) as f:
                data = json.load(f)
            reports.append({
                "report_id": data.get("report_id", report_file.stem),
                "incident_date": data.get("incident_date"),
                "location": data.get("location"),
                "severity": data.get("severity"),
                "incident_type": data.get("incident_type"),
                "follow_up_required": data.get("follow_up_required", False)
            })
        except Exception:
            continue
    return {"reports": reports, "total": len(reports)}


@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get a specific incident report by ID."""
    # Try exact match first
    report_file = REPORTS_DIR / f"{report_id}.json"
    if not report_file.exists():
        # Search for partial match
        matches = list(REPORTS_DIR.glob(f"*{report_id}*.json"))
        if not matches:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        report_file = matches[0]

    with open(report_file) as f:
        return json.load(f)


@app.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete an incident report."""
    report_file = REPORTS_DIR / f"{report_id}.json"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    report_file.unlink()
    return {"status": "deleted", "report_id": report_id}


@app.get("/reports/{report_id}/summary")
async def get_report_summary(report_id: str):
    """Get a condensed summary of a report."""
    report_file = REPORTS_DIR / f"{report_id}.json"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    with open(report_file) as f:
        data = json.load(f)

    return {
        "report_id": data.get("report_id"),
        "date": data.get("incident_date"),
        "location": data.get("location"),
        "severity": data.get("severity"),
        "description": data.get("description", "")[:300] + "...",
        "corrective_actions_count": len(data.get("corrective_actions", [])),
        "regulatory_notification": data.get("regulatory_notification_required", False)
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
