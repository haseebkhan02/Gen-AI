# nodes/parser_node.py
    
from tools.pcap_tool import parse_pcap

def parser_node(state):

    packets = parse_pcap(state["file_path"])

    steps = state.get("reasoning_steps", [])
    steps.append(f"Parsed {len(packets)} packets from PCAP")

    return {
        "packets": packets,
        "reasoning_steps": steps,
    }