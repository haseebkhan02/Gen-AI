"""
EHS AI POC - Streamlit Frontend
Clean, professional interface for safety monitoring.
"""

import streamlit as st
import requests
import json
import base64
import os
from datetime import datetime
from pathlib import Path
import io

# ─── Config ──────────────────────────────────────────────────────────────────
API_BASE = os.getenv("EHS_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="EHS AI Monitor",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0f1923 0%, #1a2d3d 50%, #0d2137 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #ff6b35;
    }

    .main-header h1 {
        color: #ffffff;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.8rem;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .main-header p {
        color: #8ba3b8;
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
    }

    .status-card {
        background: #1a2332;
        border: 1px solid #2a3f55;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }

    .severity-critical { background: #3d0f0f; border: 1px solid #ff4444; color: #ff6b6b; border-radius: 6px; padding: 0.3rem 0.8rem; font-weight: 700; font-size: 0.8rem; }
    .severity-high { background: #3d1f0f; border: 1px solid #ff8844; color: #ffaa66; border-radius: 6px; padding: 0.3rem 0.8rem; font-weight: 700; font-size: 0.8rem; }
    .severity-medium { background: #2d2d0f; border: 1px solid #ddaa00; color: #ffdd44; border-radius: 6px; padding: 0.3rem 0.8rem; font-weight: 700; font-size: 0.8rem; }
    .severity-low { background: #0f2d1a; border: 1px solid #44aa66; color: #66dd88; border-radius: 6px; padding: 0.3rem 0.8rem; font-weight: 700; font-size: 0.8rem; }
    .severity-compliant { background: #0f2d1a; border: 1px solid #00cc44; color: #44ff88; border-radius: 6px; padding: 0.3rem 0.8rem; font-weight: 700; font-size: 0.8rem; }

    .violation-card {
        background: #1c0f0f;
        border: 1px solid #ff4444;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .corrective-action {
        background: #f4f7fb;
        border-left: 3px solid #ff6b35;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 6px 6px 0;
    }

    .metric-box {
        background: #111d2b;
        border: 1px solid #1e3a50;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }

    .metric-number {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2.5rem;
        font-weight: 600;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #8ba3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }

    .policy-result {
        background: #111d2b;
        border: 1px solid #1e3a50;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .step-badge {
        display: inline-block;
        background: #ff6b35;
        color: white;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        text-align: center;
        line-height: 24px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 0.5rem;
    }

    .api-status-ok { color: #44ff88; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; }
    .api-status-err { color: #ff4444; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def api_get(endpoint: str) -> tuple[dict | None, str | None]:
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=30)
        r.raise_for_status()
        return r.json(), None
    except requests.ConnectionError:
        return None, "Cannot connect to backend API. Is it running? Run: `cd backend && python main.py`"
    except Exception as e:
        return None, str(e)


def api_post(endpoint: str, data: dict = None, files=None) -> tuple[dict | None, str | None]:
    try:
        if files:
            r = requests.post(f"{API_BASE}{endpoint}", files=files, data=data, timeout=120)
        else:
            r = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=120)
        r.raise_for_status()
        return r.json(), None
    except requests.ConnectionError:
        return None, "Cannot connect to backend API. Is it running?"
    except Exception as e:
        return None, f"API Error: {r.text if 'r' in dir() else str(e)}"


def severity_badge(severity: str) -> str:
    s = severity.upper() if severity else "UNKNOWN"
    cls_map = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low", "COMPLIANT": "compliant"}
    cls = cls_map.get(s, "low")
    return f'<span class="severity-{cls}">{s}</span>'


def render_metric(value, label: str, color: str = "#ff6b35"):
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-number" style="color: {color};">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🦺 EHS AI Monitor")
    st.markdown("---")

    # API Status
    health_data, err = api_get("/health")
    if health_data:
        st.markdown('<p class="api-status-ok">● API ONLINE</p>', unsafe_allow_html=True)
        groq_status = health_data.get("groq_api", "unknown")
        if groq_status == "configured":
            st.markdown('<p class="api-status-ok">● GROQ AI READY</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="api-status-err">● GROQ NOT CONFIGURED</p>', unsafe_allow_html=True)
            st.caption("Set GROQ_API_KEY in .env file")

        kb = health_data.get("knowledge_base", {})
        if kb.get("status") == "healthy":
            st.markdown(f'<p class="api-status-ok">● KB: {kb.get("policies", 0)} policies</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="api-status-err">● KB DEGRADED</p>', unsafe_allow_html=True)

        cv = health_data.get("cv_module", {})
        if cv.get("status") == "healthy":
            st.markdown(f'<p class="api-status-ok">● CV: {cv.get("model", "unknown")}</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="api-status-err">● API OFFLINE</p>', unsafe_allow_html=True)
        st.error(err)

    st.markdown("---")

    page = st.radio("Navigation", [
        "🔍 Analyze Image",
        "📋 Incident Reports",
        "📚 Policy Knowledge Base",
        "🏗️ Architecture"
    ])

    st.markdown("---")
    st.caption("EHS AI POC v1.0")
    st.caption("Powered by YOLOv8 + Groq LLaMA")


# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>⚡ EHS AI MONITORING SYSTEM</h1>
    <p>Computer Vision + Agentic AI for Environment, Health & Safety Compliance</p>
</div>
""", unsafe_allow_html=True)


# ─── Page: Analyze Image ─────────────────────────────────────────────────────

if page == "🔍 Analyze Image":
    st.markdown("### 🔍 Safety Compliance Analysis")
    st.markdown("Upload an image for real-time EHS compliance analysis using Computer Vision + AI reasoning.")

    col1, col2 = st.columns([1, 1])

    with col1:
        location = st.text_input("📍 Location / Area", value="Industrial Floor A", placeholder="e.g., Warehouse Zone B")
        generate_report = st.checkbox("📄 Auto-generate incident report", value=True)

        uploaded_file = st.file_uploader(
            "Upload Image",
            type=["jpg", "jpeg", "png", "bmp"],
            help="Supports JPG, PNG, BMP. Recommended: 640x480 minimum."
        )

    with col2:
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        else:
            st.markdown("""
            <div style="background:#111d2b; border:2px dashed #2a3f55; border-radius:8px; 
                        padding:3rem; text-align:center; color:#4a6a85; margin-top:1rem;">
                <div style="font-size:3rem;">📷</div>
                <div style="margin-top:0.5rem;">Upload an image to analyze</div>
                <div style="font-size:0.75rem; margin-top:0.3rem;">Safety violations will be highlighted</div>
            </div>
            """, unsafe_allow_html=True)

    # Process
    run_analysis = st.button("🚀 Run EHS Analysis", type="primary", use_container_width=True)

    if run_analysis :
        image_data = None

        if uploaded_file:
            image_bytes = uploaded_file.read()
            image_data = base64.b64encode(image_bytes).decode("utf-8")

        if image_data:
            with st.spinner("🔍 Running analysis pipeline... (CV → KB → AI → Report)"):
                steps_placeholder = st.empty()
                steps_placeholder.info("⚙️ Step 1/4: Computer vision detection...")

                result, err = api_post("/analyze/image", {
                    "image_base64": image_data,
                    "location": location,
                    "generate_report": generate_report
                })

                steps_placeholder.empty()

            if err:
                st.error(f"Analysis failed: {err}")
            elif result:
                st.success("✅ Analysis complete!")

                # ── Results Overview ──
                st.markdown("---")
                st.markdown("### 📊 Results Overview")

                cv = result.get("cv_results", {})
                assessment = result.get("assessment", {})
                summary = cv.get("summary", {})

                # Status banner
                compliance_status = assessment.get("overall_compliance_status", "UNKNOWN")
                risk_score = assessment.get("risk_score", 0)

                if compliance_status == "COMPLIANT":
                    st.success(f"✅ **COMPLIANT** — Risk Score: {risk_score}/100")
                elif compliance_status == "VIOLATION":
                    st.error(f"🚨 **VIOLATION DETECTED** — Risk Score: {risk_score}/100")
                elif compliance_status == "WARNING":
                    st.warning(f"⚠️ **WARNING** — Risk Score: {risk_score}/100")
                else:
                    st.info(f"ℹ️ **{compliance_status}** — Risk Score: {risk_score}/100")

                # Metrics row
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    render_metric(summary.get("persons_in_frame", 0), "PERSONS DETECTED", "#4a9eff")
                with m2:
                    viols = summary.get("ppe_violations", 0)
                    render_metric(viols, "PPE VIOLATIONS", "#ff4444" if viols > 0 else "#44ff88")
                with m3:
                    hazards = summary.get("hazard_count", 0)
                    render_metric(hazards, "HAZARDS", "#ffaa44" if hazards > 0 else "#44ff88")
                with m4:
                    render_metric(
                        len(assessment.get("violations", [])),
                        "POLICY VIOLATIONS",
                        "#ff4444" if assessment.get("violations") else "#44ff88"
                    )

                # ── Annotated Image ──
                annotated = cv.get("annotated_image")
                if annotated:
                    st.markdown("### 🖼️ Annotated Image")
                    st.image(
                        base64.b64decode(annotated),
                        caption="CV Analysis: Green=Compliant, Red=Violation",
                        use_column_width=True
                    )

                # ── Violations ──
                violations = assessment.get("violations", [])
                if violations:
                    st.markdown("### 🚨 Detected Violations")
                    for v in violations:
                        with st.expander(f"[{v.get('violation_id', '?')}] {v.get('violation_type', 'Unknown')} — {v.get('severity', '?')}", expanded=True):
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.markdown(f"**Description:** {v.get('description', '-')}")
                                st.markdown(f"**Policy Reference:** `{v.get('policy_reference', '-')}`")
                                st.markdown(f"**Evidence:** {v.get('evidence', '-')}")
                            with col_b:
                                st.markdown(severity_badge(v.get('severity', '')), unsafe_allow_html=True)
                                if v.get("immediate_action_required"):
                                    st.markdown("🚨 **IMMEDIATE ACTION**")

                # ── AI Reasoning ──
                reasoning = assessment.get("reasoning")
                if reasoning:
                    st.markdown("### 🤖 AI Reasoning")
                    st.info(reasoning)

                # ── Incident Report ──
                report = result.get("incident_report")
                if report:
                    st.markdown("### 📄 Generated Incident Report")
                    report_id = result.get("report_id", "")

                    r_col1, r_col2 = st.columns([2, 1])
                    with r_col1:
                        st.markdown(f"**Report ID:** `{report.get('report_id', report_id)}`")
                        st.markdown(f"**Location:** {report.get('location', location)}")
                        st.markdown(f"**Date:** {report.get('incident_date', datetime.now().isoformat())}")
                    with r_col2:
                        st.markdown(severity_badge(report.get("severity", "")), unsafe_allow_html=True)
                        if report.get("regulatory_notification_required"):
                            st.error("⚠️ Regulatory notification required!")

                    st.markdown(f"**Description:** {report.get('description', '-')}")

                    # Corrective actions
                    corrective_actions = report.get("corrective_actions", [])
                    if corrective_actions:
                        st.markdown("**Corrective Actions:**")
                        for ca in corrective_actions:
                            priority_color = {"IMMEDIATE": "#ff4444", "SHORT_TERM": "#ffaa44", "LONG_TERM": "#44aa88"}.get(ca.get("priority", ""), "#888")
                            st.markdown(f"""
                            <div class="corrective-action">
                                <strong style="color:{priority_color};">[{ca.get('priority', '?')}]</strong>
                                {ca.get('description', '-')}
                                <br><small>👤 {ca.get('responsible_party', '-')} · ⏱️ {ca.get('due_within', '-')}</small>
                            </div>
                            """, unsafe_allow_html=True)

                    # Download
                    st.download_button(
                        "⬇️ Download Report JSON",
                        data=json.dumps(report, indent=2),
                        file_name=f"{report.get('report_id', 'report')}.json",
                        mime="application/json"
                    )
                else:
                    st.info("ℹ️ No incident report generated (no violations detected or report generation disabled).")


# ─── Page: Incident Reports ───────────────────────────────────────────────────

elif page == "📋 Incident Reports":
    st.markdown("### 📋 Incident Reports")

    data, err = api_get("/reports")
    if err:
        st.error(err)
    elif data:
        reports = data.get("reports", [])
        if not reports:
            st.info("No incident reports yet. Run an analysis to generate reports.")
        else:
            st.markdown(f"**{data.get('total', 0)} total reports**")

            # Summary metrics
            severities = [r.get("severity", "LOW") for r in reports]
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_metric(sum(1 for s in severities if s == "CRITICAL"), "CRITICAL", "#ff4444")
            with c2:
                render_metric(sum(1 for s in severities if s == "HIGH"), "HIGH", "#ff8844")
            with c3:
                render_metric(sum(1 for s in severities if s == "MEDIUM"), "MEDIUM", "#ffdd44")
            with c4:
                render_metric(sum(1 for s in severities if s == "LOW"), "LOW", "#44ff88")

            st.markdown("---")

            for report in reports:
                with st.expander(
                    f"📄 {report.get('report_id', '?')} | {report.get('location', '-')} | {report.get('incident_date', '-')[:16]}",
                    expanded=False
                ):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Type:** {report.get('incident_type', '-')}")
                        st.markdown(f"**Location:** {report.get('location', '-')}")
                        if report.get("follow_up_required"):
                            st.warning("⚡ Follow-up required")
                    with col2:
                        st.markdown(severity_badge(report.get("severity", "")), unsafe_allow_html=True)

                    if st.button(f"View Full Report", key=f"view_{report.get('report_id', '')}"):
                        full, err2 = api_get(f"/reports/{report.get('report_id', '')}")
                        if full:
                            st.json(full)


# ─── Page: Knowledge Base ─────────────────────────────────────────────────────

elif page == "📚 Policy Knowledge Base":
    st.markdown("### 📚 EHS Policy Knowledge Base")
    st.markdown("Semantic search over EHS policies powered by ChromaDB + sentence-transformers.")

    # Stats
    stats_data, _ = api_get("/knowledge/stats")
    if stats_data:
        s1, s2, s3 = st.columns(3)
        with s1:
            render_metric(stats_data.get("total_policies", 0), "POLICIES INDEXED")
        with s2:
            render_metric(stats_data.get("total_chunks", 0), "KNOWLEDGE CHUNKS")
        with s3:
            render_metric(len(stats_data.get("categories", [])), "CATEGORIES")

    st.markdown("---")
    st.markdown("#### 💬 Ask a Policy Question")

    # Categories
    cats_data, _ = api_get("/knowledge/categories")
    categories = ["All Categories"] + (cats_data.get("categories", []) if cats_data else [])

    q_col1, q_col2 = st.columns([3, 1])
    with q_col1:
        question = st.text_input(
            "Your question",
            placeholder="e.g., What PPE is required in chemical handling areas?",
            label_visibility="collapsed"
        )
    with q_col2:
        cat_filter = st.selectbox("Category", categories, label_visibility="collapsed")

    # Example questions
    st.markdown("**Quick examples:**")
    examples = [
        "What PPE is required on production floors?",
        "How should chemical spills be handled?",
        "What are the confined space entry requirements?",
        "When is fall protection required?",
        "How long can hazardous waste be stored?"
    ]
    ex_cols = st.columns(len(examples))
    for i, (col, ex) in enumerate(zip(ex_cols, examples)):
        with col:
            if st.button(ex[:30] + "...", key=f"ex_{i}", help=ex):
                question = ex
                st.session_state["last_question"] = ex

    # Run query
    if question or st.session_state.get("last_question"):
        q = question or st.session_state.get("last_question", "")
        if q:
            with st.spinner("🔍 Searching knowledge base..."):
                payload = {
                    "question": q,
                    "n_results": 4,
                    "category_filter": None if cat_filter == "All Categories" else cat_filter
                }
                result, err = api_post("/knowledge/query", payload)

            if err:
                st.error(err)
            elif result:
                st.markdown(f"**Query:** *{result.get('question', q)}*")
                st.markdown(f"**Results found:** {result.get('total_results', 0)}")

                # AI Answer
                ai_answer = result.get("ai_answer", "")
                if ai_answer:
                    st.markdown("#### 🤖 AI Answer")
                    st.markdown(f"""
                    <div style="background:#111d2b; border-left:4px solid #ff6b35; 
                                padding:1rem; border-radius:0 8px 8px 0; margin-bottom:1rem;">
                        {ai_answer}
                    </div>
                    """, unsafe_allow_html=True)

                # Retrieved policies
                st.markdown("#### 📜 Retrieved Policy Sections")
                for r in result.get("retrieved_policies", []):
                    with st.expander(
                        f"[{r.get('policy_id', '?')}] {r.get('title', '-')} (score: {r.get('relevance_score', 0):.3f})",
                        expanded=False
                    ):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Category:** {r.get('category', '-')}")
                        with col2:
                            st.markdown(severity_badge(r.get("severity", "")), unsafe_allow_html=True)
                        st.markdown(r.get("content", "-")[:800])


# ─── Page: Architecture ───────────────────────────────────────────────────────

elif page == "🏗️ Architecture":
    st.markdown("### 🏗️ System Architecture")

    st.markdown("""
    #### Data Flow

    ```
    Image Input (JPEG/PNG)
         │
         ▼
    ┌─────────────────────────────────┐
    │   CV Module (YOLOv8 Nano)       │  ← Lightweight CPU model (~6MB)
    │   • Object detection            │
    │   • PPE color analysis          │
    │   • Hazard detection            │
    │   • Image annotation            │
    └──────────────┬──────────────────┘
                   │ Structured CV Output
                   ▼
    ┌─────────────────────────────────┐
    │  Knowledge Base (ChromaDB)      │  ← Local vector DB, no server needed
    │  • 10 EHS policy documents      │
    │  • sentence-transformers embed  │
    │  • Semantic similarity search   │
    └──────────────┬──────────────────┘
                   │ Relevant Policy Context
                   ▼
    ┌─────────────────────────────────┐
    │  Reasoning Agent (Groq API)     │  ← LLaMA 3.3 70B via Groq
    │  • Compliance assessment        │
    │  • Dynamic rule application     │
    │  • Incident report generation   │
    │  • Policy Q&A                   │
    └──────────────┬──────────────────┘
                   │ Structured JSON Output
                   ▼
    ┌─────────────────────────────────┐
    │  FastAPI REST Backend           │
    │  • Orchestration layer          │
    │  • Report persistence           │
    │  • API endpoints                │
    └──────────────┬──────────────────┘
                   │ HTTP REST
                   ▼
    ┌─────────────────────────────────┐
    │  Streamlit Frontend             │
    │  • Image upload & preview       │
    │  • Results visualization        │
    │  • Report management            │
    │  • Policy Q&A interface         │
    └─────────────────────────────────┘
    ```
    """)

    st.markdown("#### Component Summary")
    components = [
        ("CV Module", "YOLOv8 Nano", "~6MB model", "Object detection, PPE analysis, hazard detection"),
        ("Embeddings", "all-MiniLM-L6-v2", "~22MB model", "Local semantic search, no API needed"),
        ("Vector DB", "ChromaDB", "In-process/persistent", "Policy document indexing and retrieval"),
        ("LLM Reasoning", "LLaMA 3.3 70B via Groq", "Free API", "Compliance assessment, report generation, Q&A"),
        ("Backend", "FastAPI + uvicorn", "Python 3.9+", "REST API orchestration, report storage"),
        ("Frontend", "Streamlit", "Python 3.9+", "Web UI for all operations"),
    ]
    for name, tech, size, desc in components:
        st.markdown(f"""
        <div style="background:#111d2b; border:1px solid #1e3a50; border-radius:8px; padding:0.75rem 1rem; margin:0.4rem 0;">
            <strong style="color:#ff6b35;">{name}</strong>
            <span style="color:#8ba3b8; margin-left:0.5rem; font-size:0.85rem;">{tech} · {size}</span>
            <br><span style="font-size:0.85rem;">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### Design Decisions & Trade-offs")
    st.markdown("""
    | Decision | Choice | Rationale |
    |----------|--------|-----------|
    | CV Model | YOLOv8 Nano | Runs on CPU laptop, ~6MB, 45+ FPS |
    | PPE Detection | Color analysis (HSV) | YOLOv8-COCO lacks PPE classes; color is fast & interpretable |
    | Embeddings | MiniLM-L6-v2 | 22MB, CPU-fast, good semantic quality for policy text |
    | Vector DB | ChromaDB | Zero-config, embedded, persistent, free |
    | LLM | Groq + LLaMA 3.3 70B | Free tier, extremely fast inference, no GPU needed |
    | Reasoning | Dynamic prompting | Avoids hardcoded rules, adaptable to new policies |
    | Reports | JSON + file storage | Simple, portable, deterministic |
    """)
