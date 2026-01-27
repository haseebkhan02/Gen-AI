import streamlit as st
from typing import TypedDict, Annotated, Sequence, Dict, Any
import yfinance as yf

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_groq import ChatGroq
from langchain_core.tools import tool


# LLM FACTORY
@st.cache_resource(show_spinner=False)
def get_llm(api_key: str):
    return ChatGroq(
        model="qwen/qwen3-32b",
        api_key=api_key,
        temperature=0.1
    )

# AGENT STATE
class AgentState(TypedDict):
    company: str
    raw_data: str
    summary: str
    messages: Annotated[Sequence[BaseMessage], add_messages]

# TOOLS
@tool
def fetch_stock_data(company: str) -> str:
    """Fetch latest stock performance data for a company."""
    try:
        ticker = yf.Ticker(company)
        info = ticker.info
        hist = ticker.history(period="5d")

        current_price = info.get("currentPrice", "N/A")
        change_percent = info.get("regularMarketChangePercent", "N/A")
        market_cap = info.get("marketCap", "N/A")
        pe_ratio = info.get("trailingPE", "N/A")

        recent_performance = hist["Close"].pct_change().tail(3).mean() * 100

        return f"""
Stock Data for {company}
- Current Price: ${current_price}
- Daily Change: {change_percent:+.2f}%
- 3-Day Avg Change: {recent_performance:+.2f}%
- Market Cap: ${market_cap:,.0f}
- P/E Ratio: {pe_ratio}
"""
    except Exception as e:
        return f"Stock data unavailable for {company}: {str(e)}"

@tool
def fetch_news_data(company: str) -> str:
    """Fetch latest news headlines (mock)."""
    news = [
        f"{company} announces Q4 earnings beat",
        f"{company} partners with AI startup",
        f"Analysts raise price target for {company}",
    ]
    return "Latest News:\n" + "\n".join(f"• {n}" for n in news)


# AGENT 1 – DATA COLLECTOR
def create_data_collector(llm):
    collector_llm = llm.bind_tools([fetch_stock_data, fetch_news_data])

    def node(state: AgentState) -> Dict[str, Any]:
        company = state["company"]

        prompt = f"""
You are a Data Collection Agent.
Collect stock data and recent news for {company}.
"""

        msg = collector_llm.invoke([HumanMessage(content=prompt)])

        tool_messages = []
        raw_outputs = []

        for call in msg.tool_calls or []:
            if call["name"] == "fetch_stock_data":
                result = fetch_stock_data.invoke(call["args"])
            elif call["name"] == "fetch_news_data":
                result = fetch_news_data.invoke(call["args"])
            else:
                result = "Unknown tool"

            tool_messages.append(
                ToolMessage(
                    content=result,
                    tool_call_id=call["id"],
                    name=call["name"],
                )
            )
            raw_outputs.append(result)

        return {
            "raw_data": "\n\n".join(raw_outputs),
            "messages": [msg, *tool_messages],
        }

    return node

# AGENT 2 – ANALYST
def create_analyst(llm):
    def node(state: AgentState) -> Dict[str, Any]:
        prompt = f"""
You are a Financial Analyst.

Company: {state["company"]}

RAW DATA:
{state["raw_data"]}

Provide:
1. Executive Summary
2. Key Financial Metrics
3. Market Sentiment
4. Opportunities
5. Risks
6. Investment Recommendation
"""

        response = llm.invoke(prompt)

        return {
            "summary": response.content,
            "messages": [response],
        }

    return node

# WORKFLOW
def create_workflow(llm):
    graph = StateGraph(AgentState)
    graph.add_node("collector", create_data_collector(llm))
    graph.add_node("analyst", create_analyst(llm))

    graph.set_entry_point("collector")
    graph.add_edge("collector", "analyst")
    graph.add_edge("analyst", END)

    return graph.compile()


# STREAMLIT UI
def main():
    st.set_page_config(
        page_title="Company Intelligence Agent",
        page_icon="📈",
        layout="wide",
    )

    st.title("🤖 Company Intelligence Agent")
    st.caption("LangGraph + Groq | Multi-Agent System")

    # Sidebar
    with st.sidebar:
        st.header("🔑 Configuration")
        api_key = st.text_input("Groq API Key", type="password")

    # Inputs
    company = st.text_input("Company Ticker", placeholder="AAPL, NVDA, TSLA")
    analyze = st.button("🚀 Analyze")

    if analyze:
        if not api_key:
            st.error("Please enter Groq API key")
            return
        if not company:
            st.error("Please enter company ticker")
            return

        llm = get_llm(api_key)
        app = create_workflow(llm)

        with st.spinner("Agents collaborating..."):
            result = app.invoke({
                "company": company,
                "raw_data": "",
                "summary": "",
                "messages": [],
            })

        tab1, tab2, tab3 = st.tabs(["📊 Summary", "📈 Raw Data", "🛤 Agent Trace"])

        with tab1:
            st.markdown(result["summary"])

        with tab2:
            st.code(result["raw_data"])

        with tab3:
            for msg in result["messages"]:
                role = "Human" if isinstance(msg, HumanMessage) else "Agent"
                st.markdown(f"**{role}:** {msg.content}")

if __name__ == "__main__":
    main()
