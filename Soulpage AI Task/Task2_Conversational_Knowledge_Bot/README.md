# 🤖 Conversational Knowledge Bot (LangGraph + Groq + Streamlit)

A **multi-tool conversational AI assistant** built using **LangGraph**, **Groq LLM**, and **Streamlit**.
The bot intelligently routes user queries to **Wikipedia**, **ArXiv**, or **Web Search (DuckDuckGo)** based on the nature of the question, while maintaining full conversational context.

---

## ✨ Features

* 🔁 **Conversational Memory** – remembers previous messages in the session
* 🧠 **Tool-Aware Agent** – automatically decides when to use:

  * Wikipedia (facts, people, history)
  * ArXiv (research papers, academic topics)
  * Web Search (recent or uncertain information)
* 🔀 **LangGraph-based Agent Flow** – clean state management and tool routing
* 💬 **Chat-style UI** using Streamlit
* 🧹 **Chat History Management** – clear chat or start a new conversation
* 🎛️ **Temperature Control** from UI
* 🔐 **Secure API Key Input** (no hardcoding)

---

## 🏗️ Architecture Overview

```
User (Streamlit UI)
        ↓
LangGraph Chatbot Node
        ↓
Tool Selection (tools_condition)
        ↓
ToolNode (Wikipedia / Arxiv / Web Search)
        ↓
Chatbot Node (final response)
```

### Components

* **LLM**: Groq (`qwen/qwen3-32b`)
* **Graph Engine**: LangGraph
* **Tools**:

  * WikipediaAPIWrapper
  * DuckDuckGoSearchRun
  * ArxivQueryRun
* **Frontend**: Streamlit

---

## 📂 Project Structure

```
.
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

---

## ⚙️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/conversational-knowledge-bot.git
cd conversational-knowledge-bot
```

### 2️⃣ Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
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
langchain
langgraph
langchain-groq
langchain-core
langchain-community
ddgs
wikipedia
arxiv
```

---

## 🔑 Groq API Key

1. Get a free API key from 👉 [https://console.groq.com](https://console.groq.com)
2. Enter the API key in the **Streamlit sidebar** when prompted

⚠️ **Do NOT hardcode your API key**

---

## ▶️ Run the Application

```bash
streamlit run app.py
```

---

## 💬 How to Use

1. Enter your **Groq API Key** in the sidebar
2. Adjust **temperature** if needed
3. Ask questions like:

   * *Who is Alan Turing?*
   * *Latest research on transformers*
   * *What happened in AI last week?*
4. The agent will automatically decide which tool to use
5. Continue asking follow-up questions (context is preserved)

---

## 🧠 Tool Selection Logic

| Question Type            | Tool Used      |
| ------------------------ | -------------- |
| Facts / People / History | Wikipedia      |
| Research / Papers        | ArXiv          |
| Recent / Uncertain       | DuckDuckGo     |
| Follow-ups               | Context Memory |

---

## 🧪 Example Queries

* `"Explain attention mechanism"`
* `"Recent papers on diffusion models"`
* `"Who is Jensen Huang?"`
* `"Latest news on OpenAI"`

---

## 🚀 Future Improvements

* 📄 PDF / document upload
* 🔎 Citation-aware responses
* 🧵 Persistent memory across sessions
* ⚡ Streaming responses
* 🧠 Tool confidence scoring
* 🖼️ Multimodal inputs

---

## 🧩 Key Concepts Demonstrated

* LangGraph State Machines
* Tool-based LLM reasoning
* Agent routing with `tools_condition`
* Streamlit state management
* Production-safe API key handling

---
