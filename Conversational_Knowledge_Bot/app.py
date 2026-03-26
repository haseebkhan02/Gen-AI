import streamlit as st
from typing import TypedDict, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
#from langchain_core.tools import Tool
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun, ArxivQueryRun
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

# ---------------- STREAMLIT CONFIG ---------------- #
st.set_page_config(
    page_title="Conversational Knowledge Bot",
    page_icon="🤖",
    layout="wide"
)

st.markdown("<h1 style='text-align:center'>🤖 Conversational Knowledge Bot</h1>", unsafe_allow_html=True)

# ---------------- KNOWLEDGE TOOLS ---------------- #
wiki_api = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=3000)
duckduckgo_api = DuckDuckGoSearchRun()
arxiv_api = ArxivQueryRun()

def wikipedia_search(query: str) -> str:
    """Search Wikipedia for factual information."""
    return wiki_api.run(query)

def arxiv_search(query: str) -> str:
    """Search Arxiv for research papers."""
    results = arxiv_api.run(query)
    if isinstance(results, list):
        return "\n".join([f"{r.get('title', '')} - {r.get('link', '')}" for r in results[:5]])
    elif isinstance(results, dict):
        return "\n".join([f"{k}: {v}" for k, v in results.items()])
    return str(results)

def web_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    results = duckduckgo_api.run(query)
    if isinstance(results, list):
        return "\n".join([str(r) for r in results[:5]])
    elif isinstance(results, dict):
        return "\n".join([f"{k}: {v}" for k, v in results.items()])
    return str(results)

# Use @tool decorator instead of Tool wrapper
from langchain_core.tools import tool

@tool
def wikipedia_search_tool(query: str) -> str:
    """Search Wikipedia for factual information."""
    return wiki_api.run(query)

@tool
def arxiv_search_tool(query: str) -> str:
    """Search Arxiv for research papers."""
    results = arxiv_api.run(query)
    if isinstance(results, list):
        return "\n".join([f"{r.get('title', '')} - {r.get('link', '')}" for r in results[:5]])
    elif isinstance(results, dict):
        return "\n".join([f"{k}: {v}" for k, v in results.items()])
    return str(results)

@tool
def web_search_tool(query: str) -> str:
    """Search the web using DuckDuckGo."""
    results = duckduckgo_api.run(query)
    if isinstance(results, list):
        return "\n".join([str(r) for r in results[:5]])
    elif isinstance(results, dict):
        return "\n".join([f"{k}: {v}" for k, v in results.items()])
    return str(results)

TOOLS = [wikipedia_search_tool, arxiv_search_tool, web_search_tool]

# ---------------- GRAPH STATE ---------------- #
class GraphState(TypedDict):
    messages: List[BaseMessage]

# ---------------- SIDEBAR ---------------- #
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    groq_api_key = st.text_input(
        "GROQ API Key",
        type="password",
        help="Get it from https://console.groq.com"
    )

    temperature = st.slider("Temperature", 0.0, 1.0, 0.3)

    if st.button("🗑️ Clear Current Chat"):
        st.session_state.messages = []

    if st.button("🆕 Start New Chat"):
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if st.session_state.messages:
            st.session_state.chat_history.append(st.session_state.messages)
        st.session_state.messages = []
        st.rerun()

# ---------------- INITIALIZE ---------------- #
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if not groq_api_key:
    st.info("👈 Enter your GROQ API key to start.")
    st.stop()

# ---------------- LLM ---------------- #
llm = ChatGroq(
    groq_api_key=groq_api_key,
    model_name="qwen/qwen3-32b",
    temperature=temperature
).bind_tools(
    TOOLS,
    tool_choice="auto"
)

SYSTEM_PROMPT = """
You are a conversational knowledge assistant.

Rules:
- Remember previous conversation context.
- Use Wikipedia for well-known facts and people.
- Use Arxiv for research or academic questions.
- Use web search if information is recent or uncertain.
- Answer follow-up questions using earlier context.
"""

# ---------------- GRAPH NODES ---------------- #
def chatbot(state: GraphState):
    messages = state["messages"]

    # Inject system prompt if not already present
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm.invoke(messages)
    return {"messages": messages + [response]}

tool_node = ToolNode(TOOLS)

# ---------------- BUILD GRAPH ---------------- #
graph = StateGraph(GraphState)
graph.add_node("chatbot", chatbot)
graph.add_node("tools", tool_node)
graph.set_entry_point("chatbot")
graph.add_conditional_edges("chatbot", tools_condition)
graph.add_edge("tools", "chatbot")
graph.add_edge("chatbot", END)
app = graph.compile()

# ---------------- DISPLAY PREVIOUS CHATS ---------------- #
if st.session_state.chat_history:
    st.markdown("### 🕘 Previous Chats")
    for i, chat in enumerate(st.session_state.chat_history, 1):
        st.markdown(f"**Chat {i}:**")
        for msg in chat:
            if isinstance(msg, HumanMessage):
                st.markdown(f"**User:** {msg.content}")
            elif isinstance(msg, AIMessage):
                st.markdown(f"**Assistant:** {msg.content}")
        st.markdown("---")

# ---------------- UI RENDER CURRENT CHAT ---------------- #
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(msg.content)

# ---------------- CHAT INPUT ---------------- #
if user_input := st.chat_input("Ask me anything..."):
    st.session_state.messages.append(HumanMessage(content=user_input))

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = app.invoke({"messages": st.session_state.messages})
            new_message = result["messages"][-1]
            st.markdown(new_message.content)
            st.session_state.messages.append(new_message)
