# graph/workflow.py

from langgraph.graph import StateGraph
from graph.state import AgentState

from nodes.parser_node import parser_node
from nodes.analyzer_node import analyzer_node
from nodes.rca_node import rca_node
from nodes.summary_node import summary_node
from nodes.throughput_node import throughput_node
from graph.conditions import route_after_analysis

def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("parser", parser_node)
    builder.add_node("throughput", throughput_node)
    builder.add_node("analyzer", analyzer_node)
    builder.add_node("rca", rca_node)
    builder.add_node("summary", summary_node)

    builder.set_entry_point("parser")

    # clean linear flow
    builder.add_edge("parser", "throughput")
    builder.add_edge("throughput", "analyzer")

    builder.add_conditional_edges(
        "analyzer",
        route_after_analysis,
        {
            "rca": "rca",
            "summary": "summary"
        }
    )

    builder.add_edge("rca", "summary")

    builder.set_finish_point("summary")

    return builder.compile()