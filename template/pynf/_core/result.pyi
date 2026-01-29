"""Execution result objects and output-path extraction (stubs)."""

from __future__ import annotations

from typing import Any


class NextflowResult:
    def __init__(
        self,
        *,
        workflow_events: list[dict] | None = ...,
        file_events: list[dict] | None = ...,
        task_workdirs: list[str] | None = ...,
        work_dir: str | None = ...,
        execution_report: dict[str, Any] | None = ...,
    ) -> None: ...

    def get_output_files(self) -> list[str]: ...
    def get_workflow_outputs(self) -> list[dict[str, Any]]: ...
    def get_execution_report(self) -> dict[str, Any]: ...
    def get_stdout(self) -> str: ...
