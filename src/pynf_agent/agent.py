"""
Agent orchestration for bioinformatics workflows.

Provides the main agent class and session context for tracking workflow state.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from smolagents import ToolCallingAgent, LiteLLMModel

from .openrouter_client import OpenRouterClient


class SessionContext:
    """Manages state across agent conversation and workflow executions."""

    def __init__(self, working_dir: Optional[str] = None):
        """
        Initialize session context.

        Args:
            working_dir: Directory for storing workflow outputs (default: ./agent_workspace)
        """
        self.working_dir = Path(working_dir or "./agent_workspace")
        self.working_dir.mkdir(parents=True, exist_ok=True)

        self.execution_history: List[Dict[str, Any]] = []
        self._execution_counter = 0

    def add_execution(
        self,
        module: str,
        inputs: Optional[List[Dict]] = None,
        params: Optional[Dict] = None,
        outputs: Optional[List[str]] = None,
        status: str = "success",
        error: Optional[str] = None
    ) -> int:
        """
        Add an execution record.

        Args:
            module: Module name/path that was executed
            inputs: Input parameters passed to module
            params: Additional parameters
            outputs: List of output file paths
            status: Execution status (success/failed)
            error: Error message if failed

        Returns:
            Execution ID
        """
        execution_id = self._execution_counter
        self._execution_counter += 1

        record = {
            "id": execution_id,
            "module": module,
            "inputs": inputs,
            "params": params,
            "outputs": outputs or [],
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

        self.execution_history.append(record)
        return execution_id

    def get_execution(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """Get execution record by ID."""
        for record in self.execution_history:
            if record["id"] == execution_id:
                return record
        return None

    def get_latest_execution(self) -> Optional[Dict[str, Any]]:
        """Get the most recent execution record."""
        if self.execution_history:
            return self.execution_history[-1]
        return None

    def get_outputs(self, execution_id: Optional[int] = None) -> List[str]:
        """
        Get output file paths.

        Args:
            execution_id: Specific execution ID, or None for latest

        Returns:
            List of output file paths
        """
        if execution_id is not None:
            record = self.get_execution(execution_id)
        else:
            record = self.get_latest_execution()

        if record:
            return record.get("outputs", [])
        return []

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions."""
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r["status"] == "success")
        failed = total - successful

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "latest": self.get_latest_execution()
        }


class BioinformaticsAgent:
    """
    Interactive agent for bioinformatics workflow automation.

    Uses smollagents with OpenRouter LLM to execute nf-core modules through
    natural language conversation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        working_dir: Optional[str] = None,
        tools: Optional[List] = None
    ):
        """
        Initialize bioinformatics agent.

        Args:
            api_key: OpenRouter API key (defaults to env var)
            model: Model identifier (defaults to claude-3.5-sonnet)
            working_dir: Directory for workflow outputs
            tools: List of Tool instances to provide to agent
        """
        # Initialize OpenRouter client
        self.openrouter_client = OpenRouterClient(api_key=api_key, model=model)

        # Initialize session context
        self.context = SessionContext(working_dir=working_dir)

        # Create LiteLLM model for smolagents
        # LiteLLM supports OpenRouter by using the model name with openrouter/ prefix
        model_name = f"openrouter/{self.openrouter_client.model}"

        # Set up environment for LiteLLM
        os.environ["OPENROUTER_API_KEY"] = self.openrouter_client.api_key

        self.model = LiteLLMModel(
            model_id=model_name,
            api_base=self.openrouter_client.base_url
        )

        # Initialize agent with tools
        self.tools = tools or []
        self.agent = ToolCallingAgent(
            tools=self.tools,
            model=self.model,
        )

    def set_tools(self, tools: List):
        """
        Update the agent's tools and reinitialize the ToolCallingAgent.

        Args:
            tools: List of Tool instances
        """
        self.tools = tools
        self.agent = ToolCallingAgent(
            tools=self.tools,
            model=self.model,
        )

    def chat(self, message: str) -> str:
        """
        Send a message to the agent and get response.

        Args:
            message: User message

        Returns:
            Agent response
        """
        try:
            response = self.agent.run(message)
            return response
        except Exception as e:
            return f"Error during agent execution: {e}"

    def get_context(self) -> SessionContext:
        """Get the current session context."""
        return self.context

    def get_model_info(self) -> dict:
        """Get information about the configured model."""
        return self.openrouter_client.get_model_info()
