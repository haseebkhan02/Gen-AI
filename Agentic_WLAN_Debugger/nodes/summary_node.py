# nodes/summary_node.py

from llm.groq_client import get_llm

def summary_node(state):

    llm = get_llm(state["api_key"])

    content = state.get("root_cause")

    if not content:
        content = state.get("analysis")

    # optional enhancement: include throughput context
    throughput_info = state.get("throughput_drop")

    response = llm.invoke(f"""
    Summarize WLAN firmware debugging results.

    Throughput Drop Detected: {throughput_info}

    Findings:
    {content}
    """).content

    steps = state.get("reasoning_steps", [])
    steps.append("Generated summary")

    return {
        "summary": response,
        "reasoning_steps": steps
    }