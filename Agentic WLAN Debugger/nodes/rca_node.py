# nodes/rca_node.py

from llm.groq_client import get_llm

def rca_node(state):
    llm = get_llm(state["api_key"])

    response = llm.invoke(
        f"Find root cause:\n{state['analysis']}"
    ).content

    steps = state.get("reasoning_steps", [])
    steps.append("Performed root cause analysis")

    return {
        "root_cause": response,
        "reasoning_steps": steps
    }