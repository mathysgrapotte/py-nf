"""
Demo script for pynf-agent - Programmatic usage example.

This script demonstrates how to use the BioinformaticsAgent programmatically
rather than through the interactive CLI.

Run with: uv run python examples/agent_demo.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynf_agent import BioinformaticsAgent
from pynf_agent.tools import (
    WebSearchTool,
    ListNFCoreModulesTool,
    ListSubmodulesTool,
    GetModuleInfoTool,
    RunNFModuleTool,
    ListOutputFilesTool,
    ReadFileTool,
    ListDirectoryTool,
)


def main():
    """Run agent demo."""
    print("=" * 70)
    print("pynf-agent Demo - Programmatic Usage")
    print("=" * 70)

    # Check for API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("\nError: OPENROUTER_API_KEY environment variable not set.")
        print("Please set your OpenRouter API key:")
        print("  export OPENROUTER_API_KEY='your-key-here'")
        print("Or add it to a .env file in your project directory.")
        return 1

    # Initialize agent
    print("\n[1] Initializing agent...")
    agent = BioinformaticsAgent(
        working_dir="./agent_workspace_demo"
    )

    # Get session context
    context = agent.get_context()

    # Initialize tools
    tools = [
        WebSearchTool(),
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

    model_info = agent.get_model_info()
    print(f"  Model: {model_info['model']}")
    print(f"  Workspace: {Path('./agent_workspace_demo').absolute()}")

    # Example conversations
    examples = [
        "List some available nf-core modules",
        "What submodules are available for samtools?",
        "Get detailed information about the fastqc module",
    ]

    for i, query in enumerate(examples, 1):
        print(f"\n[{i + 1}] Query: {query}")
        print("-" * 70)

        response = agent.chat(query)
        print(f"Response:\n{response}\n")

    # Show execution summary
    print("\n" + "=" * 70)
    print("Execution Summary")
    print("=" * 70)

    summary = context.get_execution_summary()
    print(f"Total executions: {summary['total_executions']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")

    if summary['latest']:
        print(f"\nLatest execution:")
        print(f"  Module: {summary['latest']['module']}")
        print(f"  Status: {summary['latest']['status']}")

    print("\n✓ Demo completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
