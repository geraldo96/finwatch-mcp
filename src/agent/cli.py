"""Interactive CLI client for the finwatch LangGraph agent.

Run: python -m src.agent.cli
"""

import asyncio

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from langchain_core.messages import HumanMessage

from src.agent.graph import get_compiled_graph

console = Console()


async def main():
    """Run the interactive CLI."""
    console.print(
        Panel.fit(
            "[bold green]finwatch-mcp[/bold green] — Financial Portfolio Agent\n"
            "Ask questions about your portfolio in natural language.\n"
            "Type [bold]quit[/bold] or [bold]exit[/bold] to stop.",
            border_style="green",
        )
    )

    graph = get_compiled_graph()

    while True:
        try:
            query = console.input("\n[bold cyan]You>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not query or query.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        console.print("[dim]Thinking...[/dim]")

        try:
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=query)]}
            )

            # Extract the final assistant message
            for msg in reversed(result["messages"]):
                if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_call_id"):
                    console.print()
                    console.print(
                        Panel(
                            Markdown(msg.content),
                            title="[bold green]Agent[/bold green]",
                            border_style="green",
                        )
                    )
                    break

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    asyncio.run(main())
