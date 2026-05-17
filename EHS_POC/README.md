# 🦺 EHS AI POC — Environment Health & Safety Monitoring

An end-to-end agentic AI system for industrial safety compliance monitoring using computer vision and LLM-powered reasoning.

---

## 📐 Architecture Overview

```
Image Input
    │
    ▼
┌──────────────────┐     ┌────────────────────┐
│  CV Module       │────▶│  Knowledge Base     │
│  YOLOv8 Nano     │     │  ChromaDB + MiniLM  │
│  + HSV Analysis  │     │  10 EHS Policies    │
└──────────────────┘     └────────┬───────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │  Reasoning Agent   │
                         │  Groq LLaMA 3.3 70B│
                         └────────┬───────────┘
                                  │
                         ┌────────▼───────────┐
                         │  FastAPI Backend   │
                         │  REST API Server   │
                         └────────┬───────────┘
                                  │
                         ┌────────▼───────────┐
                         │  Streamlit UI      │
                         └────────────────────┘
```

## 🗂️ Project Structure

```
ehs_poc/
├── backend/
│   ├── main.py                 # FastAPI application & orchestration
│   ├── cv_module.py            # Computer vision pipeline (YOLOv8 + HSV)
│   ├── reasoning_agent.py      # Groq-powered agentic reasoning
│   └── knowledge_base_module.py # ChromaDB RAG system
├── frontend/
│   └── app.py                  # Streamlit web interface
├── knowledge_base/
│   └── ehs_policies.json       # 10 EHS policy documents
├── data/
│   └── chroma_db/              # Auto-created vector DB storage
├── reports/                    # Auto-created incident reports (JSON)
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- ~500MB disk space (models download on first run)
- Free Groq API key: https://console.groq.com

### 2. Install Dependencies

```bash
# Clone the repo
git clone <repo-url>
cd ehs_poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

`.env` file:
```
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
YOLO_MODEL_SIZE=n
CONFIDENCE_THRESHOLD=0.45
```

### 4. Start the Backend

```bash
cd backend
python main.py
# API starts at http://localhost:8000
# Docs at http://localhost:8000/docs
```

On first run, these will download automatically:
- `yolov8n.pt` — ~6MB YOLOv8 Nano model
- `all-MiniLM-L6-v2` — ~22MB sentence transformer

### 5. Start the Frontend

```bash
# In a new terminal
cd frontend
streamlit run app.py
# UI opens at http://localhost:8501
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info |
| `GET` | `/health` | System health check |
| `POST` | `/analyze/image` | Analyze base64 image |
| `POST` | `/analyze/upload` | Upload image file |
| `POST` | `/knowledge/query` | Query EHS policies |
| `GET` | `/knowledge/categories` | List policy categories |
| `GET` | `/reports` | List all reports |
| `GET` | `/reports/{id}` | Get specific report |

### Example: Analyze an Image

```bash
# Upload a file
curl -X POST "http://localhost:8000/analyze/upload" \
  -F "file=@/path/to/image.jpg" \
  -F "location=Warehouse A" \
  -F "generate_report=true"
```

```bash
# Base64 image
curl -X POST "http://localhost:8000/analyze/image" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<base64_string>",
    "location": "Lab Zone B",
    "generate_report": true
  }'
```

### Example: Query Policies

```bash
curl -X POST "http://localhost:8000/knowledge/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What PPE is required in chemical handling areas?",
    "n_results": 3
  }'
```

---

## 📋 EHS Policies Included

| ID | Policy | Severity |
|----|--------|----------|
| PPE-001 | Personal Protective Equipment | HIGH |
| FIRE-001 | Fire Safety & Evacuation | CRITICAL |
| CHEM-001 | Chemical Handling & Storage | HIGH |
| ELEC-001 | Electrical Safety (LOTO) | CRITICAL |
| FALL-001 | Fall Protection | CRITICAL |
| ERGON-001 | Ergonomics & Manual Handling | MEDIUM |
| FORKLIFT-001 | Forklift Safety | HIGH |
| WASTE-001 | Waste Management & Housekeeping | MEDIUM |
| INCIDENT-001 | Incident Reporting | HIGH |
| CONFINED-001 | Confined Space Entry | CRITICAL |

---

## 📤 Sample Output

### Compliance Assessment
```json
{
  "overall_compliance_status": "VIOLATION",
  "confidence_level": "HIGH",
  "violations": [{
    "violation_id": "V001",
    "policy_reference": "PPE-001",
    "violation_type": "PPE_MISSING",
    "description": "2 persons detected without hard hats in production floor area",
    "severity": "HIGH",
    "evidence": "CV analysis: 2 persons, 0 hard hat colors in head regions",
    "immediate_action_required": true
  }],
  "risk_score": 65,
  "reasoning": "CV detected 2 workers without visible PPE in an industrial area..."
}
```

### Incident Report
```json
{
  "report_id": "INC-202506101430-001",
  "severity": "HIGH",
  "incident_type": "PPE Non-Compliance",
  "corrective_actions": [{
    "action_id": "CA-001",
    "description": "Stop work immediately and provide PPE to all personnel",
    "priority": "IMMEDIATE",
    "responsible_party": "Area Supervisor",
    "due_within": "1 hour"
  }],
  "regulatory_references": ["OSHA 29 CFR 1910.132"]
}
```

---

## ⚙️ Design Decisions

| Aspect | Decision | Reason |
|--------|----------|--------|
| CV model | YOLOv8 Nano | Tiny (6MB), CPU-only, fast enough for laptops |
| PPE detection | HSV color analysis | COCO-trained YOLO lacks PPE classes; color is effective & explainable |
| Embeddings | all-MiniLM-L6-v2 | 22MB, great quality, no API key, runs on CPU |
| Vector DB | ChromaDB embedded | Zero-config, persistent, runs in-process |
| LLM | Groq LLaMA 3.3 70B | Free tier, very fast, avoids hardcoded rules |
| Reasoning temp | 0.1 | Deterministic, reproducible compliance outputs |
| Report storage | JSON files | Simple, portable, audit trail |

## ⚠️ Assumptions

1. Images are representative of real-time video frames
2. PPE compliance judged by color analysis (yellow/white = hard hat, high-vis = vest)
3. YOLO COCO classes used as proxy; production would use fine-tuned safety dataset
4. Groq free tier sufficient for POC (rate limits apply)
5. Single-location deployment assumed

---

## 🔮 Production Extensions

- Fine-tune YOLOv8 on labeled safety dataset (hard hats, vests, goggles, gloves)
- Add video stream support (RTSP camera feeds)
- PostgreSQL for report storage with audit trail
- Multi-site support with location hierarchies  
- Email/SMS alerts for critical violations
- Dashboard with trend analytics
- Mobile app for field inspections
- Integration with CMMS/ERP systems
