# Agentic AI Powered Environment Health & Safety (EHS) Monitoring System

An end-to-end Agentic AI based Environment Health & Safety (EHS) monitoring system integrating Computer Vision, RAG (Retrieval Augmented Generation), and LLM-based reasoning for automated safety compliance monitoring and incident generation.

---

# Problem Statement

Industrial and laboratory environments require continuous monitoring for:

- PPE compliance
- Restricted area violations
- Unsafe working conditions
- Policy adherence

Manual monitoring is:
- expensive
- inconsistent
- difficult to scale

This project demonstrates an AI-driven solution capable of:

 Detecting safety violations from images/videos  
 Reasoning over EHS policies  
 Generating structured incident reports  
 Answering EHS-related questions using RAG  
 Providing explainable and traceable outputs  

---

# Features

## Computer Vision
- PPE Detection
- Helmet detection
- Safety vest detection
- Person detection
- Unsafe condition identification

## Agentic AI Workflow
- Multi-agent architecture
- Dynamic policy reasoning
- Violation evaluation
- Corrective action generation

## RAG-based Knowledge Retrieval
- Query EHS documents
- Retrieve SOP/policy context
- Context-aware responses

## Incident Management
- Structured incident reports
- Severity classification
- Corrective/preventive actions
- SQL Server persistence

## Frontend & APIs
- Streamlit dashboard
- FastAPI backend
- REST APIs

---

# System Architecture

```text
                ┌────────────────────┐
                │   Streamlit UI     │
                └─────────┬──────────┘
                          │
                    REST API Calls
                          │
                ┌─────────▼──────────┐
                │     FastAPI        │
                └─────────┬──────────┘
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
     ▼                    ▼                    ▼
CV Detection        Agentic Reasoning      RAG Engine
(YOLOv8)            (Groq LLM)             (FAISS)

     │                    │                    │
     └────────────┬───────┴────────────┬──────┘
                  ▼                    ▼
         Incident Generator      Policy Retrieval

                  ▼
        Microsoft SQL Server
````

---

# Tech Stack

| Layer           | Technology            |
| --------------- | --------------------- |
| Frontend        | Streamlit             |
| Backend         | FastAPI               |
| Computer Vision | YOLOv8                |
| LLM             | Groq + Llama 3        |
| RAG             | LangChain + FAISS     |
| Embeddings      | Sentence Transformers |
| Database        | Microsoft SQL Server  |
| ORM             | SQLAlchemy            |
| Deployment      | Docker                |

---

---

# Setup Instructions

# 1. Clone Repository

```bash
git clone https://github.com/your-username/agentic-ai-ehs-monitoring-system.git

cd EHS_POC_DOCKER_SQL_SERVER
```

---

# 2. Create Virtual Environment

## Windows

```bash
python -m venv venv

venv\\Scripts\\activate
```

## Linux/Mac

```bash
python3 -m venv venv

source venv/bin/activate
```

---

# 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 4. Configure Environment Variables

Create `.env`

```env
GROQ_API_KEY=your_groq_api_key

DB_SERVER=localhost
DB_NAME=EHS_DB
DB_USER=ehs_user
DB_PASSWORD=YourStrongPassword123
```

---

# 5. Create SQL Server Database

```sql
CREATE DATABASE EHS_DB;
```

---

# 6. Create Tables

```bash
python create_tables.py
```

---

# 7. Ingest EHS Documents

Place PDF documents inside:

```text
data/documents/
```

Then run:

```bash
python app/rag/ingest.py
```

---

# 8. Run FastAPI Backend

```bash
uvicorn app.api.main:app --reload
```

Backend runs at:

```text
http://localhost:8000
```

---

# 9. Run Streamlit Frontend

```bash
streamlit run streamlit_app/app.py
```

Frontend runs at:

```text
http://localhost:8501
```

---

# Sample Workflow

## Step 1

Upload safety image.

## Step 2

YOLOv8 detects:

* person
* helmet
* vest

## Step 3

Violation extraction module evaluates:

* missing helmet
* missing vest

## Step 4

RAG retrieves relevant EHS policies.

## Step 5

Groq LLM reasons over:

* detections
* policies
* safety context

## Step 6

Structured incident report generated.

## Step 7

Incident saved into Microsoft SQL Server.

---

# API Endpoints

## Root Endpoint

```http
GET /
```

---

## Analyze Image

```http
POST /analyze
```

### Input

Image file

### Output

```json
{
  "detections": [],
  "violations": [],
  "policy_context": "",
  "report": {}
}
```

---

## Get Incidents

```http
GET /incidents
```

Returns all stored incidents.

---

# Example Incident Report

```json
{
  "incident_id": 12,
  "timestamp": "2026-05-22 10:15:12",
  "severity": "HIGH",
  "reason": "Worker detected without helmet in restricted zone.",
  "corrective_actions": [
    "Stop worker entry",
    "Provide safety helmet",
    "Conduct PPE compliance training"
  ]
}
```

---

# Datasets Used

## PPE Detection

* Roboflow PPE Dataset
* Hard Hat Workers Dataset
* Construction Safety Dataset

## Documents

* OSHA Safety Manuals
* Laboratory SOP PDFs
* Industrial EHS Policies

---

# Agentic Workflow

The system uses modular agents:

| Agent           | Responsibility            |
| --------------- | ------------------------- |
| Vision Agent    | Detect safety conditions  |
| Retrieval Agent | Retrieve policy context   |
| Reasoning Agent | Determine violations      |
| Report Agent    | Generate incident reports |

---

# Security Best Practices

* Secrets stored in `.env`
* `.env` excluded using `.gitignore`
* Dedicated SQL Server user
* Deterministic LLM outputs
* Structured JSON responses

---

# Docker Support

## Build Image

```bash
docker build -t ehs-ai .
```

## Run Container

```bash
docker run -p 8000:8000 ehs-ai
```

---

# Future Improvements

* Real-time CCTV monitoring
* Multi-camera support
* DeepSORT tracking
* Alerting system
* Email/SMS notifications
* Dashboard analytics
* Azure deployment
* LangGraph orchestration
* PDF incident export

---

# Assumptions

* PPE dataset available
* SQL Server installed locally
* GPU optional but recommended
* Documents provided in PDF format

---

# Evaluation Goals Covered

 Computer Vision
 Agentic AI
 Multi-step workflow
 RAG implementation
 Structured outputs
 REST APIs
 Explainable reasoning
 Enterprise-grade storage

---

#  Author

Haseeb Khan

```
