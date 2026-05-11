# nodes/analyzer_node.py

from llm.groq_client import get_llm

def analyzer_node(state):

    llm = get_llm(state["api_key"])

    sample = state["packets"][:200]

    # ✅ Use already computed throughput signal
    throughput_drop = state.get("throughput_drop", False)

    response = llm.invoke(f"""
    You are analyzing WLAN firmware behavior.

    Inputs:
    - Throughput Drop Detected (system metric): {throughput_drop}

    Task:
    1. Detect network anomalies (retries, auth failures, delays)
    2. Correlate with throughput condition
    3. Identify if firmware issue is likely

    Output format:
    ANOMALY: YES/NO
    EXPLANATION:
    """).content

    anomaly = "ANOMALY: YES" in response.upper()

    steps = state.get("reasoning_steps", [])
    steps.append("Analyzed WLAN behavior with throughput context")

    return {
        "analysis": response,
        "anomaly_detected": anomaly,
        "reasoning_steps": steps
    }