# nodes/ throughput_node.py
import pandas as pd

def throughput_node(state):

    packets = state["packets"]

    df = pd.DataFrame(packets)

    # Safe guards
    if df.empty or "time" not in df:
        return {
            "throughput_data": {},
            "throughput_drop": False,
            "reasoning_steps": state.get("reasoning_steps", [])
        }

    # Convert timestamps safely
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])

    # Packet size safe conversion
    df["length"] = pd.to_numeric(df.get("length", 0), errors="coerce").fillna(0)

    # Throughput calculation
    throughput = (
        df.groupby(df["time"].dt.floor("1s"))["length"]
        .sum()
        .reset_index()
    )

    throughput["mbps"] = (throughput["length"] * 8) / 1e6

    avg_tp = throughput["mbps"].mean() if not throughput.empty else 0
    min_tp = throughput["mbps"].min() if not throughput.empty else 0

    # Detect drop
    drop_detected = avg_tp > 0 and min_tp < (0.5 * avg_tp)

    steps = state.get("reasoning_steps", [])
    steps.append(f"Calculated throughput. Avg={avg_tp:.2f} Mbps, Min={min_tp:.2f} Mbps")

    return {
        # better format for visualization
        "throughput_data": throughput.to_dict(orient="list"),
        "throughput_drop": drop_detected,
        "reasoning_steps": steps
    }