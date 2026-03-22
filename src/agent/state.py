"""LangGraph agent state definition."""

from dataclasses import dataclass, field
from typing import Annotated

from langgraph.graph.message import add_messages


@dataclass
class AgentState:
    """State schema for the finwatch agent.

    Tracks conversation messages, tool results, and reasoning steps.
    """

    # Conversation history (LangGraph message reducer)
    messages: Annotated[list, add_messages] = field(default_factory=list)

    # Current tool results (cleared each reasoning cycle)
    tool_results: list[dict] = field(default_factory=list)

    # Number of reasoning steps taken
    step_count: int = 0

    # Whether the agent should stop
    should_stop: bool = False
