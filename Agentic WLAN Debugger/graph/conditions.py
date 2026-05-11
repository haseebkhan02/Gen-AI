# graph/conditions.py
def route_after_analysis(state):

    anomaly = state.get("anomaly_detected", False)
    throughput_drop = state.get("throughput_drop", False)

    # If ANY critical issue exists → RCA
    if anomaly or throughput_drop:
        return "rca"

    return "summary"