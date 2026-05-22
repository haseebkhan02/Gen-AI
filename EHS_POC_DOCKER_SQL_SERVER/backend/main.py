"""
EHS AI POC - FastAPI Backend
Main API server orchestrating CV, reasoning, knowledge base, and report generation.
"""

import json
import logging
import os
import uuid
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from database import (
    create_db_engine,
    init_db,
    ReportRepository
)

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

# ─── DATABASE INIT ───────────────────────────────────────────────────────────
db_engine = create_db_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=db_engine
)

report_repo = ReportRepository(SessionLocal)

# ─── LIFESPAN EVENT (REPLACES on_event) ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        logger.info("Initializing SQL Server...")

        # Connect to master database
        master_engine = create_db_engine(database="master")

        # Create ehs_db if missing
        with master_engine.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as conn:

            conn.execute(text("""
                IF DB_ID('ehs_db') IS NULL
                CREATE DATABASE ehs_db
            """))

        logger.info("ehs_db verified/created")

        # Initialize tables
        init_db(db_engine)

        logger.info("SQL Server initialized successfully")

    except Exception as e:
        logger.error(f"DB init failed: {e}", exc_info=True)

    yield

    logger.info("Shutting down EHS API...")

# ─── APP SETUP ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="EHS AI POC API",
    description="Agentic AI for Environment Health & Safety Monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── MODULE INITIALIZATION ──────────────────────────────────────────────────
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", str(BASE_DIR / "reports")))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_BASE_DIR = Path(
    os.getenv("KNOWLEDGE_BASE_DIR", str(BASE_DIR / "knowledge_base"))
)

CHROMA_DB_DIR = str(
    Path(os.getenv("CHROMA_DB_DIR", str(BASE_DIR / "data" / "chroma_db")))
)

# Lazy-loaded modules
_cv_detector = None
_knowledge_base = None
_reasoning_agent = None


def get_cv_detector():
    global _cv_detector

    if _cv_detector is None:
        from cv_module import SafetyDetector

        confidence = float(
            os.getenv("CONFIDENCE_THRESHOLD", "0.45")
        )

        person_model = os.getenv(
            "PERSON_MODEL_PATH",
            str(BASE_DIR / "models" / "yolov8s.pt")
        )

        ppe_model = os.getenv(
            "PPE_MODEL_PATH",
            str(BASE_DIR / "models" / "ppe_detection.pt")
        )

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

        policies_path = str(
            KNOWLEDGE_BASE_DIR / "ehs_policies.json"
        )

        _knowledge_base = EHSKnowledgeBase(
            persist_dir=CHROMA_DB_DIR,
            policies_path=policies_path
        )

    return _knowledge_base


def get_reasoning_agent():
    global _reasoning_agent

    if _reasoning_agent is None:
        from reasoning_agent import EHSReasoningAgent

        model = os.getenv(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile"
        )

        _reasoning_agent = EHSReasoningAgent(model=model)

    return _reasoning_agent

# ─── REQUEST MODELS ──────────────────────────────────────────────────────────
class PolicyQueryRequest(BaseModel):
    question: str
    category_filter: Optional[str] = None
    n_results: int = 4


class AnalyzeImageRequest(BaseModel):
    image_base64: str
    location: str = "Industrial Floor A"
    generate_report: bool = True

# ─── API ENDPOINTS ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "EHS AI POC",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.post("/analyze/image")
async def analyze_image_base64(request: AnalyzeImageRequest):

    try:
        logger.info("Running CV pipeline...")

        detector = get_cv_detector()

        cv_results = detector.process_image(
            request.image_base64
        )

        logger.info("Querying KB...")

        kb = get_knowledge_base()

        query_parts = []

        if cv_results["summary"]["ppe_violations"] > 0:
            query_parts.append("PPE requirements")

        for hazard in cv_results["hazards_detected"]:
            query_parts.append(
                hazard["type"].replace("_", " ")
            )

        query_parts.append("safety compliance")

        query = " ".join(query_parts)

        kb_results = kb.query(query, n_results=5)

        policy_context = "\n\n".join([
            f"[{r['policy_id']} - {r['title']}]\n{r['content']}"
            for r in kb_results["results"]
        ])

        logger.info("Running reasoning agent...")

        agent = get_reasoning_agent()

        assessment = agent.assess_compliance(
            cv_results,
            policy_context
        )

        report = None
        report_id = None

        if request.generate_report and (
            assessment.get("overall_compliance_status")
            in ["VIOLATION", "WARNING"]
            or cv_results["summary"]["requires_review"]
        ):

            report = agent.generate_incident_report(
                assessment,
                cv_results,
                policy_context,
                request.location
            )

            report_id = report.get("report_id")

            # Save only to SQL Server
            full_report = {
                **report,
                "cv_results_summary": cv_results["summary"],
                "assessment": {
                    k: v for k, v in assessment.items()
                    if k != "raw_llm_response"
                },
                "kb_policies_used": [
                    r["policy_id"]
                    for r in kb_results["results"]
                ],
                "annotated_image": cv_results.get("annotated_image")
            }

            report_repo.save(
                report_dict=full_report,
                cv_results=cv_results,
                assessment=assessment
            )

            logger.info(
                f"Saved to SQL Server: {report_id}"
            )

        return {
            "status": "success",
            "cv_results": cv_results,
            "assessment": assessment,
            "incident_report": report,
            "report_id": report_id,
            "report_saved": report is not None
        }

    except Exception as e:
        logger.error(e, exc_info=True)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/analyze/upload")
async def analyze_upload(file: UploadFile = File(...)):

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid image"
        )

    contents = await file.read()

    image_b64 = base64.b64encode(contents).decode("utf-8")

    return await analyze_image_base64(
        AnalyzeImageRequest(
            image_base64=image_b64
        )
    )


@app.post("/knowledge/query")
async def query_kb(request: PolicyQueryRequest):

    kb = get_knowledge_base()

    results = kb.query(
        request.question,
        n_results=request.n_results
    )

    return results

# ─── REPORT APIs ─────────────────────────────────────────────────────────────

@app.get("/reports")
async def list_reports():
    return report_repo.list_all()


@app.get("/reports/{report_id}")
async def get_report(report_id: str):

    report = report_repo.get_by_id(report_id)

    if not report:
        raise HTTPException(status_code=404)

    return report


@app.delete("/reports/{report_id}")
async def delete_report(report_id: str):

    ok = report_repo.delete(report_id)

    if not ok:
        raise HTTPException(status_code=404)

    return {
        "status": "deleted"
    }

# ─── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", 8000)),
        reload=True
    )