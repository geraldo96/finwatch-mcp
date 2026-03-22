"""Agent nodes for the LangGraph finwatch agent.

Nodes:
- reason_node: Uses Claude to analyze the situation and decide next action
- tool_node: Executes MCP tool calls
- should_continue: Routing function (tools vs end)
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.agent.state import AgentState
from src.mcp_server.config import settings

# Tools available to the agent (matching MCP server tools)
AGENT_TOOLS = [
    {
        "name": "get_portfolio",
        "description": "Get current portfolio holdings, P&L, and sector allocation",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Optional ticker filter"},
            },
        },
    },
    {
        "name": "analyze_risk",
        "description": "Calculate risk metrics: VaR, Sharpe, Beta, drawdown, volatility",
        "input_schema": {
            "type": "object",
            "properties": {
                "window_days": {"type": "integer", "default": 30},
                "confidence_level": {"type": "number", "default": 0.95},
            },
        },
    },
    {
        "name": "detect_anomaly",
        "description": "Detect unusual price/volume movements in portfolio",
        "input_schema": {
            "type": "object",
            "properties": {
                "lookback_days": {"type": "integer", "default": 7},
                "z_threshold": {"type": "number", "default": 2.0},
            },
        },
    },
    {
        "name": "search_filings",
        "description": "Semantic search over SEC filings (RAG)",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "ticker": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_market_kpi",
        "description": "Get macro indicators: rates, inflation, sector performance",
        "input_schema": {
            "type": "object",
            "properties": {
                "indicators": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "compliance_check",
        "description": "Check portfolio against concentration and exposure limits",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_single_stock_pct": {"type": "number", "default": 15.0},
                "max_sector_pct": {"type": "number", "default": 40.0},
            },
        },
    },
]

SYSTEM_PROMPT = """You are a financial portfolio analyst assistant powered by the finwatch-mcp system.

You have access to tools that query real market data, analyze portfolio risk, detect anomalies,
search SEC filings, check compliance, and retrieve macro indicators.

Guidelines:
- Always start by understanding what the user needs before calling tools
- Chain multiple tool calls when needed for comprehensive analysis
- Provide clear, actionable insights — not just raw data
- Flag risks and violations prominently
- When uncertain, explain your reasoning and ask for clarification
- Format financial numbers clearly (e.g., $1,234.56, 12.5%)

You are speaking to a portfolio manager or financial analyst who wants data-driven answers."""


def _get_llm():
    """Get the Claude LLM instance."""
    return ChatAnthropic(
        model=settings.claude_model,
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )


async def reason_node(state: AgentState) -> dict:
    """Reasoning node: Claude analyzes the conversation and decides next action."""
    llm = _get_llm()
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state.messages

    response = await llm_with_tools.ainvoke(messages)

    return {
        "messages": [response],
        "step_count": state.step_count + 1,
    }


async def tool_node(state: AgentState) -> dict:
    """Tool execution node: runs the tools requested by Claude."""
    # Import tool handlers
    from src.mcp_server.tools.portfolio import get_portfolio
    from src.mcp_server.tools.risk import analyze_risk
    from src.mcp_server.tools.anomaly import detect_anomaly
    from src.mcp_server.tools.filings import search_filings
    from src.mcp_server.tools.market_kpi import get_market_kpi
    from src.mcp_server.tools.compliance import compliance_check

    handlers = {
        "get_portfolio": get_portfolio,
        "analyze_risk": analyze_risk,
        "detect_anomaly": detect_anomaly,
        "search_filings": search_filings,
        "get_market_kpi": get_market_kpi,
        "compliance_check": compliance_check,
    }

    last_message = state.messages[-1]
    tool_messages = []

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            handler = handlers.get(tool_call["name"])
            if handler:
                try:
                    result = await handler(**tool_call["args"])
                except Exception as e:
                    result = f"Error: {str(e)}"
            else:
                result = f"Unknown tool: {tool_call['name']}"

            tool_messages.append(
                ToolMessage(content=result, tool_call_id=tool_call["id"])
            )

    return {"messages": tool_messages}


def should_continue(state: AgentState) -> str:
    """Decide whether to call tools or finish."""
    # Stop if max steps reached
    if state.step_count >= settings.max_agent_steps:
        return "end"

    # Check if last message has tool calls
    last_message = state.messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "end"
