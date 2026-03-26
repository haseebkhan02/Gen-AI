import streamlit as st
import os
import re
import requests
from typing import Dict, Any, TypedDict
import json
import numpy as np
from dataclasses import dataclass
from bs4 import BeautifulSoup

from langgraph.graph import StateGraph, END

# SESSION INIT
if "api_key_set" not in st.session_state:
    st.session_state["api_key_set"] = False

st.set_page_config(
    page_title=" Paper Evaluator",
    page_icon="🧑‍⚖️",
    layout="wide"
)

# API KEY

def check_api_key():
    return bool(st.session_state.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))

def set_api_key(key: str):
    st.session_state["GROQ_API_KEY"] = key.strip()
    os.environ["GROQ_API_KEY"] = key.strip()
    st.session_state["api_key_set"] = True
    st.rerun()

# DATA

@dataclass
class PaperSection:
    title: str
    content: str
    word_count: int
    token_count: int


class GraphState(TypedDict):
    sections: Dict[str, PaperSection]
    title: str
    raw_content: Dict[str, Any]

    consistency_score: float
    grammar_score: float
    novelty_score: float
    fact_check_score: float
    fabrication_prob: float

    overall_score: float
    report: str


# SCRAPER

class ArxivScraper:
    @staticmethod
    def get_arxiv_id(url: str):
        match = re.search(r'arxiv\.org/(abs|pdf)/(\d+\.\d+)', url)
        return match.group(2) if match else None

    @staticmethod
    def scrape_arxiv(url: str):
        arxiv_id = ArxivScraper.get_arxiv_id(url)
        if not arxiv_id:
            return {"error": "Invalid URL"}

        try:
            page = requests.get(f"https://arxiv.org/abs/{arxiv_id}")
            soup = BeautifulSoup(page.content, "html.parser")

            title = soup.find("h1", class_="title").get_text().replace("Title:", "").strip()
            abstract = soup.find("blockquote", class_="abstract").get_text().replace("Abstract:", "").strip()

            return {
                "title": title,
                "abstract": abstract,
                "full_text": (title + " " + abstract)[:20000]
            }

        except Exception as e:
            return {"error": str(e)}

# LLM

def get_llm():
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate

    api_key = st.session_state.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

    return ChatGroq(
        groq_api_key=api_key,
        model_name="openai/gpt-oss-120b",
        temperature=0.1,
        max_tokens=2000
    ), ChatPromptTemplate


# AGENTS

def run_agent(prompt_text, state, key, is_fabrication=False):
    llm, ChatPromptTemplate = get_llm()

    text = state["sections"]["full_text"].content[:6000]
    title = state["title"]

    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm

    result = chain.invoke({"text": text, "title": title})

    try:
        content = result.content
        data = json.loads(content[content.find("{"):content.rfind("}") + 1])
    except:
        data = {}

    if is_fabrication:
        state["fabrication_prob"] = float(data.get("probability", 0.1))
    else:
        state[key] = float(data.get("score", 5.0))

    return state


def consistency_node(state):
        return run_agent("""
    Evaluate consistency (0-10).
    TEXT:
    {text}
    Return JSON:
    {{"score": 8.5}}
    """, state, "consistency_score")


def grammar_node(state):
    return run_agent("""
    Evaluate grammar quality (0-10).
    TEXT:
    {text}
    Return JSON:
    {{"score": 9.0}}
    """, state, "grammar_score")


def novelty_node(state):
    return run_agent("""
    Evaluate novelty (0-10).
    TITLE:
    {title}
    TEXT:
    {text}
    Return JSON:
    {{"score": 9.5}}
    """, state, "novelty_score")


def factcheck_node(state):
    return run_agent("""
    Evaluate factual correctness (0-10).
    TEXT:
    {text}
    Return JSON:
    {{"score": 8.5}}
    """, state, "fact_check_score")


def fabrication_node(state):
    return run_agent("""
    Detect fabrication probability.
    TEXT:
    {text}
    Return JSON:
    {{"probability": 0.05}}
    """, state, None, True)


def aggregate_node(state):
    avg = np.mean([
        state["consistency_score"],
        state["grammar_score"],
        state["novelty_score"],
        state["fact_check_score"]
    ])
    state["overall_score"] = avg * (1 - state["fabrication_prob"])
    return state


def report_node(state):
    llm, ChatPromptTemplate = get_llm()

    prompt = ChatPromptTemplate.from_template("""
    Generate structured evaluation report:
    Title: {title}
    Consistency Score: {c}/100
    Grammar: {g}
    Novelty Index:
    Explain novelty in 1-2 lines.

    Fact Check: {f}/100
    Fact Check Log:
    - List 2 verified claims
    - List 1 potential weak/unverified claim

    Fabrication Risk: {fab}%
    Executive Decision: PASS or FAIL
    Recommendation + Summary (100 words max)
    """)

    chain = prompt | llm

    res = chain.invoke({
        "title": state["title"],
        "c": int(state["consistency_score"] * 10),
        "g": "High" if state["grammar_score"] > 8 else "Medium",
        "n": "High" if state["novelty_score"] > 8 else "Moderate",
        "f": int(state["fact_check_score"] * 10),
        "fab": round(state["fabrication_prob"] * 100, 2)
    })

    state["report"] = res.content
    return state


# GRAPH

def build_graph():
    g = StateGraph(GraphState)

    g.add_node("consistency", consistency_node)
    g.add_node("grammar", grammar_node)
    g.add_node("novelty", novelty_node)
    g.add_node("factcheck", factcheck_node)
    g.add_node("fabrication", fabrication_node)
    g.add_node("aggregate", aggregate_node)
    g.add_node("report", report_node)

    g.set_entry_point("consistency")

    g.add_edge("consistency", "grammar")
    g.add_edge("grammar", "novelty")
    g.add_edge("novelty", "factcheck")
    g.add_edge("factcheck", "fabrication")
    g.add_edge("fabrication", "aggregate")
    g.add_edge("aggregate", "report")
    g.add_edge("report", END)

    return g.compile()


# PIPELINE

def run_evaluation(url):
    raw = ArxivScraper.scrape_arxiv(url)

    if "error" in raw:
        st.error(raw["error"])
        return

    sections = {
        "full_text": PaperSection("full", raw["full_text"], 0, 0)
    }

    graph = build_graph()
    with st.sidebar:
        st.subheader("🔁 Agent Workflow")
        graph_png = build_graph().get_graph().draw_mermaid_png()
        st.image(graph_png, use_container_width=True)

    state = {
        "sections": sections,
        "title": raw["title"],
        "raw_content": raw,
        "consistency_score": 0,
        "grammar_score": 0,
        "novelty_score": 0,
        "fact_check_score": 0,
        "fabrication_prob": 0,
        "overall_score": 0,
        "report": ""
    }

    result = graph.invoke(state)
    st.session_state.update(result)

# UI
def main():

    if not check_api_key():
        st.title("🔑 Enter API Key")
        key = st.text_input("Groq API Key", type="password")

        if st.button("Submit"):
            if key:
                set_api_key(key)
            else:
                st.error("Enter key")

        st.stop()

    st.title("Arxiv Paper Evaluator")

    url = st.text_input("Enter arXiv URL")

    if st.button("Run Evaluation"):
        run_evaluation(url)

    if "overall_score" in st.session_state:
        st.metric("Overall Score", f"{st.session_state['overall_score']:.2f}")
        st.write(st.session_state["report"])


if __name__ == "__main__":
    main()