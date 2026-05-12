# graph/state.py

from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    file_path: str
    packets: Optional[List]
    analysis: Optional[str]
    root_cause: Optional[str]
    summary: Optional[str]
    anomaly_detected: Optional[bool]
    reasoning_steps: List[str]
    api_key: str
    throughput_data: Optional[dict]
    throughput_drop: Optional[bool]
    retry_rate: Optional[float]
    avg_rssi: Optional[float]
    severity: Optional[str]
    firmware_issue: Optional[bool]
    packet_statistics: Optional[dict]