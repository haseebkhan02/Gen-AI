# EHS AI POC

Agentic AI system for Environment, Health & Safety (EHS) monitoring using:

* FastAPI backend
* Streamlit frontend
* YOLOv8 Computer Vision
* Groq LLM reasoning
* SQL Server database
* Dockerized deployment

---

# Features

* PPE detection using YOLOv8
* Hazard detection
* AI-powered compliance reasoning
* Incident report generation
* SQL Server persistence
* Knowledge base semantic search
* Streamlit dashboard UI
* Dockerized backend + frontend + SQL Server

---

# Project Structure

```text
EHS_POC/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── cv_module.py
│   ├── reasoning_agent.py
│   ├── knowledge_base_module.py
│   └── reports/
│
├── frontend/
│   └── app.py
│
├── knowledge_base/
│   └── ehs_policies.json
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
```

---

# Tech Stack

## Backend

* FastAPI
* SQLAlchemy
* PyODBC
* Uvicorn

## Frontend

* Streamlit

## AI / ML

* YOLOv8
* Groq LLM
* ChromaDB

## Database

* Microsoft SQL Server

## Containerization

* Docker
* Docker Compose

---

# Environment Variables (.env)

Create a `.env` file in project root:

```env
# GROQ
GROQ_API_KEY=YOUR_API_KEY
GROQ_MODEL=openai/gpt-oss-120b

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# CV
YOLO_MODEL_SIZE=s
CONFIDENCE_THRESHOLD=0.25
PERSON_MODEL_PATH=./models/yolov8s.pt
PPE_MODEL_PATH=./models/ppe_detection.pt

# Database
MSSQL_SERVER=sqlserver
MSSQL_PORT=1433
MSSQL_DATABASE=ehs_db
MSSQL_USER=sa
MSSQL_PASSWORD=EHS_Strong_Pass1!

# Paths
REPORTS_DIR=./reports
KNOWLEDGE_BASE_DIR=./knowledge_base
CHROMA_DB_DIR=./data/chroma_db
```

---

# Running with Docker

## Build Docker Images

```bash
docker compose build --no-cache
```

---

## Start Containers

```bash
docker compose up --build
```

Or:

```bash
docker compose up -d
```

---

# SQL Server Setup

## SQL Server Instance

```text
SQLEXPRESS
```

---

## Windows Authentication Connection String

```text
Server=localhost\SQLEXPRESS;Database=master;Trusted_Connection=True;
```

---

## SQL Login Credentials

### SA User

```text
Username: sa
Password: EHS_Strong_Pass1!
```

### Custom User

```text
Username: ehs_user
Password: StrongPass@123
```

---

## Connect via SSMS / Azure Data Studio

```text
Server: localhost\SQLEXPRESS
Authentication: SQL Login
Username: sa
Password: EHS_Strong_Pass1!
```

---

# API Endpoints

## Swagger Docs

```text
http://localhost:8000/docs
```

## Health Endpoint

```text
http://localhost:8000/health
```

## Frontend UI

```text
http://localhost:8501
```

---

# API Examples

## Get All Reports

```bash
curl http://localhost:8000/reports
```

## Filter Reports

```bash
curl "http://localhost:8000/reports?severity=HIGH&limit=20"
```

---

# Health Endpoint Example

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }
```


## Required Streamlit Binding

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

---

## Required Docker Port Mapping

```yaml
ports:
  - "8501:8501"
```

---

# Common Issues Faced

## SQL Server Issues

* Cannot open database `ehs_db`
* SQL login failure
* TCP/IP disabled
* SQL Browser service disabled
* Port 1433 blocked

---

## Docker Issues

* Build cache issues
* Persistent volume issues
* WSL disk not shrinking
* Port conflicts
* Docker networking issues

---

## Backend Issues

* FastAPI startup DB errors
* Missing `/health` endpoint
* ODBC Driver 18 missing
* SQLAlchemy connection issues

---

## Frontend Issues

* Streamlit unable to reach backend
* API URL mismatch
* CORS issues
* External IP inaccessible

---

## Firewall / Network Issues

Blocked Ports:

* 8000
* 8501
* 1433

Potential Issues:

* Missing port forwarding
* Windows Firewall rules
* ISP/public IP restrictions

---

# Recommended Fresh Rebuild Flow

```bash
docker compose down -v
docker system prune -a --volumes -f
docker builder prune -a -f
docker compose up --build
```

---

# Backend Services

The backend container runs:

* FastAPI
* SQLAlchemy
* CV pipeline
* Reasoning agent
* Knowledge base

---

# Frontend Services

The frontend container runs:

* Streamlit dashboard UI

---

# Author

Haseeb Khan
