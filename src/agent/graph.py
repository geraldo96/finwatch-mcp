"""LangGraph agent graph for finwatch.

Orchestrates multi-step reasoning over the MCP server tools.
"""

from langgraph.graph import END, StateGraph

from src.agent.state import AgentState
from src.agent.nodes import reason_node, tool_node, should_continue
from src.mcp_server.config import settings


def build_agent_graph() -> StateGraph:
    """Build the LangGraph StateGraph for the finwatch agent.

    Flow:
        start → reason → (tool_call?) → tool → reason → ... → end

    The agent reasons about the user query, decides which tools to call,
    executes them, and synthesizes the results. Stops after max_steps
    or when the agent decides it has enough information.
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("reason", reason_node)
    graph.add_node("tools", tool_node)

    # Set entry point
    graph.set_entry_point("reason")

    # Conditional edges: after reasoning, either call tools or finish
    graph.add_conditional_edges(
        "reason",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # After tool execution, go back to reasoning
    graph.add_edge("tools", "reason")

    return graph


def get_compiled_graph():
    """Get the compiled agent graph ready for invocation."""
    graph = build_agent_graph()
    return graph.compile()
