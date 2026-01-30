"""Minimal Seqera Platform API client."""

from __future__ import annotations

from typing import Any

class SeqeraClient:
    """Small HTTP client for Seqera Platform workflows."""

    ...

    def __init__(self, api_endpoint: str, access_token: str) -> None: ...
    def create_workflow_launch(
        self,
        launch: dict[str, Any],
        workspace_id: int,
        source_workspace_id: int | None = None,
    ) -> str:
        """Submit a workflow launch and return the workflow id."""
        ...

    def describe_workflow(
        self,
        workflow_id: str,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        """Return workflow metadata from the API."""
        ...

    def wait_for_workflow(
        self,
        workflow_id: str,
        workspace_id: int | None = None,
        poll_interval: float = 10.0,
        terminal_states: set[str] | None = None,
    ) -> dict[str, Any]:
        """Poll workflow status until a terminal state is reached."""
        ...
