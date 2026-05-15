# nodes/throughput_node.py

import pandas as pd

def throughput_node(state):

    packets = state.get("packets", [])

    df = pd.DataFrame(packets)

    # SAFETY CHECKS
    if df.empty:
        steps = state.get("reasoning_steps", [])
        steps.append("No packets available for throughput analysis")

        return {
            "throughput_data": {},
            "throughput_drop": False,
            "reasoning_steps": steps
        }

    if "time" not in df.columns:
        steps = state.get("reasoning_steps", [])
        steps.append("No timestamp field found")

        return {
            "throughput_data": {},
            "throughput_drop": False,
            "reasoning_steps": steps
        }

    # TIME PROCESSING
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])

    if df.empty:
        steps = state.get("reasoning_steps", [])
        steps.append("All packet timestamps invalid")

        return {
            "throughput_data": {},
            "throughput_drop": False,
            "reasoning_steps": steps
        }

    # LENGTH PROCESSING
    if "length" not in df.columns:
        df["length"] = 0

    df["length"] = (
        pd.to_numeric(df["length"], errors="coerce")
        .fillna(0)
        .astype(float)
    )

    # CALCULATE DURATION
    start_time = df["time"].min()
    end_time = df["time"].max()

    duration_seconds = (end_time - start_time).total_seconds()

    if duration_seconds <= 0:
        duration_seconds = 1

    # TOTAL THROUGHPUT
    total_bytes = df["length"].sum()

    total_bits = total_bytes * 8

    avg_mbps = total_bits / duration_seconds / 1_000_000

    # PER-SECOND THROUGHPUT
    throughput = (
        df.groupby(df["time"].dt.floor("1s"))["length"]
        .sum()
        .reset_index()
    )

    throughput["mbps"] = (
        throughput["length"] * 8
    ) / 1_000_000

    # PACKET RATE
    packets_per_sec = len(df) / duration_seconds

    # DROP DETECTION
    if not throughput.empty:

        min_mbps = throughput["mbps"].min()
        max_mbps = throughput["mbps"].max()

        # Drop if throughput falls below 40% of peak
        throughput_drop = (
            max_mbps > 0 and
            min_mbps < (0.4 * max_mbps)
        )

    else:
        min_mbps = 0
        max_mbps = 0
        throughput_drop = False

    # REASONING TRACE
    steps = state.get("reasoning_steps", [])

    steps.append(
        f"Throughput Analysis → "
        f"Avg={avg_mbps:.6f} Mbps | "
        f"Peak={max_mbps:.6f} Mbps | "
        f"Min={min_mbps:.6f} Mbps | "
        f"Packets/sec={packets_per_sec:.2f}"
    )

    return {

        "throughput_data": throughput.to_dict(orient="list"),

        "throughput_drop": throughput_drop,

        "throughput_summary": {
            "avg_mbps": round(avg_mbps, 6),
            "peak_mbps": round(max_mbps, 6),
            "min_mbps": round(min_mbps, 6),
            "packets_per_sec": round(packets_per_sec, 2),
            "duration_sec": round(duration_seconds, 2),
            "total_packets": len(df),
            "total_bytes": int(total_bytes)
        },

        "reasoning_steps": steps
    }