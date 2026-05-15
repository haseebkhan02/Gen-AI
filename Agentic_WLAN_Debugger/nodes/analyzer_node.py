# nodes/analyzer_node.py

from llm.groq_client import get_llm
import pandas as pd


def analyzer_node(state):

    llm = get_llm(state["api_key"])

    packets = state["packets"][:100]

    throughput_drop = state.get(
        "throughput_drop",
        False
    )

    df = pd.DataFrame(packets)

    # =========================
    # BASIC METRICS ONLY
    # =========================

    total_packets = len(df)

    protocol_distribution = {}

    if "protocol" in df.columns:
        protocol_distribution = (
            df["protocol"]
            .value_counts()
            .head(3)
            .to_dict()
        )

    retry_count = 0

    if "retry" in df.columns:
        retry_count = (
            df["retry"]
            .astype(str)
            .eq("1")
            .sum()
        )

    avg_rssi = None

    if "rssi" in df.columns:
        avg_rssi = (
            pd.to_numeric(
                df["rssi"],
                errors="coerce"
            ).mean()
        )

    avg_packet_length = 0

    if "length" in df.columns:
        avg_packet_length = (
            pd.to_numeric(
                df["length"],
                errors="coerce"
            ).mean()
        )

    # =========================
    # VERY SMALL PROMPT
    # =========================

    prompt = f"""
Analyze WLAN health.

Packets: {total_packets}

Protocols: {protocol_distribution}

Retries: {retry_count}

Average RSSI: {avg_rssi}

Average Length: {avg_packet_length}

Throughput Drop: {throughput_drop}

Detect:
- anomalies
- throughput issues
- possible firmware instability

Return short concise output only.
"""

    response = llm.invoke(prompt).content

    anomaly = (
        "anomaly" in response.lower()
        or "issue" in response.lower()
    )

    steps = state.get(
        "reasoning_steps",
        []
    )

    steps.append(
        "Analyzed summarized WLAN metrics"
    )

    return {
        "analysis": response,
        "anomaly_detected": anomaly,
        "reasoning_steps": steps
    }