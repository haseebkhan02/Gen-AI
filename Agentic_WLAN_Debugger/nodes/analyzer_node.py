# nodes/analyzer_node.py

from llm.groq_client import get_llm
def analyzer_node(state):
    llm = get_llm(state["api_key"])

    packets = state["packets"][:200]
    throughput_drop = state.get("throughput_drop", False)

    sample_text = "\n".join([
        f"time={p.get('time','')} proto={p.get('protocol','')} "
        f"src={p.get('src','')} dst={p.get('dst','')} "
        f"len={p.get('length',0)} retry={p.get('retry',0)} rssi={p.get('rssi','')}"
        for p in packets
    ])

    response = llm.invoke(f"""
You are analyzing WLAN firmware behavior.

Throughput Drop Detected: {throughput_drop}

Sample Packets (up to 200):
{sample_text}

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