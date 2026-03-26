---

# 📈 Company Intelligence Agent (Multi-Agent System)

A **multi-agent financial analysis application** built using **LangGraph**, **Groq LLM**, and **Streamlit**.
The system uses **two collaborating agents** to automatically collect market data and generate professional investment insights for any public company.
See the demo at https://professionalinvestmentinsightsmultiagentsystem.streamlit.app/
---

## ✨ Features

* 🤖 **Agentic Architecture** using LangGraph
* 📊 **Live Stock Data** via Yahoo Finance
* 📰 **News Signal Integration** (mock, extensible)
* 🧠 **Two-Agent Collaboration**

  * **Data Collector Agent** – gathers stock metrics & news
  * **Analyst Agent** – generates insights & recommendations
* 🔁 **Shared State Memory** across agents
* 💬 **Clean Streamlit UI**
* 🔐 **Secure API key input (no hardcoding)**
* ⚡ **Fast inference with Groq LLM (Qwen 32B)**

---

## 🏗️ System Architecture

```
User (Streamlit UI)
        ↓
LangGraph Orchestrator
        ↓
Data Collector Agent
  ├─ fetch_stock_data (Yahoo Finance)
  └─ fetch_news_data
        ↓
Analyst Agent
        ↓
Final Market Summary
```

---

## 🧩 Agent Responsibilities

### 🧠 Agent 1 – Data Collector

* Fetches:

  * Current stock price
  * Daily & recent performance
  * Market cap & P/E ratio
  * Recent company news
* Uses LangChain **tools**

### 📊 Agent 2 – Analyst

* Produces:

  * Executive Summary
  * Financial Metrics Overview
  * Market Sentiment
  * Opportunities & Risks
  * Investment Recommendation

---

## 📂 Project Structure

```
.
├── app.py              # Main Streamlit application
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
```

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/company-intelligence-agent.git
cd company-intelligence-agent
```

### 2️⃣ Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 📦 Requirements (`requirements.txt`)

```txt
streamlit
langgraph
langchain
langchain-core
langchain-groq
yfinance
```

---

## 🔑 Groq API Key Setup

1. Get a free API key from
   👉 [https://console.groq.com](https://console.groq.com)
2. Enter the API key in the **Streamlit sidebar**

⚠️ **Never hardcode API keys**

---

## ▶️ Run the Application

```bash
streamlit run app.py
```

---

## 🖥️ How to Use

1. Enter your **Groq API Key**
2. Enter a **company ticker** (e.g. `AAPL`, `NVDA`, `TSLA`)
3. Click **Analyze**
4. View:

   * 📊 Investment summary
   * 📈 Raw collected data
   * 🛤 Agent reasoning trace

---

## 🧪 Example Inputs

| Ticker | Company   |
| ------ | --------- |
| AAPL   | Apple Inc |
| NVDA   | NVIDIA    |
| TSLA   | Tesla     |
| MSFT   | Microsoft |

---

## 🧠 Key Concepts Demonstrated

* LangGraph state-based agent orchestration
* Tool-calling with LangChain
* Multi-agent collaboration
* Dependency injection of LLMs
* Production-safe API handling
* Financial data analysis automation

---

## 🚀 Future Enhancements

* 🔴 Real-time news API (NewsAPI / Alpha Vantage)
* 📉 Technical indicators (RSI, MACD, Moving Averages)
* 📊 Price & volume charts
* 🧠 Agent memory across sessions
* 📁 PDF / earnings report analysis
* ⚡ Streaming responses

---

## 👨‍💻 Author

**Haseeb Khan**
Machine Learning • Generative AI • Agentic Systems
📍 India

---

## ⭐ Support

If you find this project useful:

* ⭐ Star the repository
* 🍴 Fork and extend
* 💬 Share feedback

---