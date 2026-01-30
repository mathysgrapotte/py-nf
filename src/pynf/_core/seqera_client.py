"""Minimal Seqera Platform API client."""

from __future__ import annotations

import time
from typing import Any

import requests


class SeqeraClient:
    """Small HTTP client for Seqera Platform workflows."""

    def __init__(self, api_endpoint: str, access_token: str) -> None:
        self._api_endpoint = api_endpoint.rstrip("/")
        self._access_token = access_token

    def create_workflow_launch(
        self,
        launch: dict[str, Any],
        workspace_id: int,
        source_workspace_id: int | None = None,
    ) -> str:
        payload = {"launch": launch}
        params: dict[str, Any] = {"workspaceId": workspace_id}
        if source_workspace_id is not None:
            params["sourceWorkspaceId"] = source_workspace_id
        data = self._request("post", "/workflow/launch", params=params, json=payload)
        workflow_id = data.get("workflowId") if isinstance(data, dict) else None
        if not workflow_id:
            raise RuntimeError("Seqera API did not return workflowId")
        return str(workflow_id)

    def describe_workflow(
        self,
        workflow_id: str,
        workspace_id: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if workspace_id is not None:
            params["workspaceId"] = workspace_id
        data = self._request("get", f"/workflow/{workflow_id}", params=params)
        if not isinstance(data, dict):
            raise RuntimeError("Seqera API returned unexpected response")
        return data

    def wait_for_workflow(
        self,
        workflow_id: str,
        workspace_id: int | None = None,
        poll_interval: float = 10.0,
        terminal_states: set[str] | None = None,
    ) -> dict[str, Any]:
        terminal = terminal_states or {"SUCCEEDED", "FAILED", "CANCELLED"}
        while True:
            data = self.describe_workflow(workflow_id, workspace_id=workspace_id)
            status = _extract_status(data)
            if status in terminal:
                return data
            time.sleep(poll_interval)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._api_endpoint}{path}"
        response = requests.request(
            method,
            url,
            headers=self._headers(),
            params=params,
            json=json,
            timeout=60,
        )
        if response.status_code == 204:
            return None
        if not response.ok:
            raise RuntimeError(
                f"Seqera API request failed ({response.status_code}): {response.text}"
            )
        return response.json()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }


def _extract_status(payload: dict[str, Any]) -> str | None:
    workflow = payload.get("workflow") if isinstance(payload, dict) else None
    if isinstance(workflow, dict):
        return workflow.get("status")
    return None
