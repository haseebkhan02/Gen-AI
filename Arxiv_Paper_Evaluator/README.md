# Agentic Research Paper Evaluator (LangGraph)

An AI-powered **multi-agent system** that automatically evaluates research papers from arXiv and generates a structured **peer-review report**.

This project leverages **LangGraph** to orchestrate specialized AI agents that simulate an academic peer-review process — going beyond summarization to perform **critical analysis, scoring, and judgement**.

---

##  Problem Statement

The rapid growth of research papers on platforms like arXiv makes it difficult for researchers to:

* Assess paper quality quickly
* Verify claims and consistency
* Evaluate novelty and contribution

Traditional LLM tools often:

* Hallucinate
* Miss logical inconsistencies
* Fail at structured evaluation

 This project solves that using an **Agentic AI approach**.

---

##  Solution Overview

This system builds a **LangGraph-based multi-agent pipeline**, where each agent performs a specific evaluation task:

```
Consistency → Grammar → Novelty → FactCheck → Fabrication → Aggregate → Report
```

Each node is an independent **LLM-powered evaluator**, ensuring modular and scalable analysis.

---

##  Key Features

###  1. arXiv Paper Scraper

* Extracts:

  * Title
  * Abstract
* Cleans and prepares input for LLM processing

---

###  2. Agentic AI Workflow (LangGraph)

Built using LangGraph, the system includes:

| Agent             | Responsibility                             |
| ----------------- | ------------------------------------------ |
| Consistency Agent | Checks if methodology supports results     |
| Grammar Agent     | Evaluates academic writing quality         |
| Novelty Agent     | Estimates originality and contribution     |
| Fact-Check Agent  | Validates claims and correctness           |
| Fabrication Agent | Detects hallucination or suspicious claims |

---

###  3. Structured Evaluation Metrics

* **Consistency Score:** 0–100
* **Grammar Rating:** High / Medium / Low
* **Novelty Index:** Qualitative
* **Fact Check Score:** 0–100
* **Fabrication Risk:** % probability
* **Overall Score:** Weighted final score

---

###  4. Automated Peer Review Report

The system generates a **professional academic review** including:

* Recommendation (Accept / Reject / Revision)
* Strengths
* Weaknesses
* Summary

---

###  5. Streamlit UI

Built with Streamlit:

* Enter arXiv URL
* Input API key securely
* View results instantly
* Interactive experience

---

##  System Architecture

```
User Input (arXiv URL)
        ↓
Web Scraper
        ↓
Text Processing
        ↓
LangGraph Pipeline
        ↓
Multi-Agent Evaluation
        ↓
Score Aggregation
        ↓
Final Report Generation
```

---

##  Tech Stack

* Python
* LangGraph
* LangChain
* Streamlit
* Groq API
* BeautifulSoup (Web Scraping)
* NumPy / Pandas

---

##  Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/agentic-paper-evaluator.git
cd agentic-paper-evaluator
```

---

### 2. Create Virtual Environment

```bash
python -m venv myEnv
myEnv\Scripts\activate   # Windows
# source myEnv/bin/activate   # Mac/Linux
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

##  API Key Setup

This project uses **Groq LLM API**.

###  Option 1 (Recommended)

Enter API key directly in Streamlit UI.

###  Option 2 (Environment Variable)

```bash
set GROQ_API_KEY=your_api_key     # Windows
export GROQ_API_KEY=your_api_key  # Mac/Linux
```

---

##  Run the Application

```bash
streamlit run app.py
```

Then open:

```
http://localhost:8501
```

---

##  Example Input

```
https://arxiv.org/abs/1706.03762
```

---

## Example Output

```
Overall Score: 9.06

Consistency Score: 90/100
Grammar: High
Novelty: High
Fact Check: 95/100
Fabrication Risk: 2%

Recommendation: Accept
```

---

##  How It Works

1. User inputs arXiv link
2. System scrapes paper metadata
3. Text is passed through LangGraph pipeline
4. Each agent evaluates independently
5. Scores are aggregated
6. Final structured report is generated

---

## 🚀 Future Improvements

* 🌐 Real-time fact-check APIs
* ⚡ Parallel agent execution
* 🧠 RAG-based evaluation
* 📊 Paper comparison dashboard

---

##  Demo
Check the demo here : https://arxivpaperevaluator.streamlit.app/

---

##  Author

**Haseeb Khan**
AI / ML Engineer

---

##  License

MIT License
