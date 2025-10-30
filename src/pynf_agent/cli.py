"""
CLI for pynf-agent - Interactive bioinformatics workflow assistant.
"""

import click
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .agent import BioinformaticsAgent
from .tools import (
    ListNFCoreModulesTool,
    ListSubmodulesTool,
    GetModuleInfoTool,
    RunNFModuleTool,
    ListOutputFilesTool,
    ReadFileTool,
    ListDirectoryTool,
)

console = Console()


def print_banner():
    """Print welcome banner."""
    banner = """
# pynf-agent

**Interactive AI Assistant for Bioinformatics Workflows**

Powered by Nextflow + OpenRouter + smollagents

Type your requests in natural language and the agent will:
- Search for and download nf-core modules
- Execute bioinformatics workflows
- Inspect outputs and results

Type 'exit' or 'quit' to end the session.
"""
    console.print(Panel(Markdown(banner), border_style="blue"))


@click.command()
@click.option(
    "--model",
    default=None,
    help="OpenRouter model to use (default: anthropic/claude-3.5-sonnet)",
)
@click.option(
    "--workspace",
    default="./agent_workspace",
    help="Working directory for agent outputs (default: ./agent_workspace)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def main(model: str, workspace: str, verbose: bool):
    """
    Interactive AI agent for bioinformatics workflow automation.

    The agent can discover, configure, and execute nf-core modules through
    natural language conversation.

    Example:
        pynf-agent
        > Run quality control on my sample.fastq file using fastqc
    """
    # Check for API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        console.print(
            "[red]Error: OPENROUTER_API_KEY environment variable not set.[/red]\n"
            "Please set your OpenRouter API key:\n"
            "  export OPENROUTER_API_KEY='your-key-here'\n"
            "Or add it to a .env file in your project directory."
        )
        return

    try:
        # Print banner
        print_banner()

        # Initialize agent
        with console.status("[bold green]Initializing agent..."):
            agent = BioinformaticsAgent(
                model=model,
                working_dir=workspace,
            )

            # Get session context to pass to tools
            context = agent.get_context()

            # Initialize tools with session context
            tools = [
                ListNFCoreModulesTool(),
                ListSubmodulesTool(),
                GetModuleInfoTool(),
                RunNFModuleTool(session_context=context),
                ListOutputFilesTool(session_context=context),
                ReadFileTool(),
                ListDirectoryTool(),
            ]

            # Set tools (this reinitializes the ToolCallingAgent)
            agent.set_tools(tools)

        # Show configuration
        model_info = agent.get_model_info()
        console.print(f"\n[green]✓[/green] Agent initialized")
        console.print(f"  Model: [cyan]{model_info['model']}[/cyan]")
        console.print(f"  Workspace: [cyan]{Path(workspace).absolute()}[/cyan]")
        console.print()

        # Interactive loop
        while True:
            try:
                # Get user input
                user_input = console.input("[bold blue]>[/bold blue] ")

                # Check for exit commands
                if user_input.strip().lower() in ["exit", "quit", "q"]:
                    console.print("\n[yellow]Goodbye![/yellow]")
                    break

                # Skip empty input
                if not user_input.strip():
                    continue

                # Send to agent
                with console.status("[bold green]Agent is thinking..."):
                    response = agent.chat(user_input)

                # Display response
                console.print(f"\n[bold green]Agent:[/bold green]")
                console.print(Panel(response, border_style="green"))
                console.print()

            except KeyboardInterrupt:
                console.print("\n\n[yellow]Use 'exit' or 'quit' to end the session.[/yellow]\n")
                continue
            except EOFError:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    main()
