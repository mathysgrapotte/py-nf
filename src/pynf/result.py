"""Result objects returned from Nextflow execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import outputs as _outputs
from .jvm_values import to_python


class NextflowResult:
    """A stable, event-based result for a single Nextflow execution.

    This object intentionally avoids holding on to live JVM objects. All the data
    it exposes is captured (snapshotted) during execution.

    Attributes:
        workflow_events: Captured workflow output events.
        file_events: Captured file publish events.
        task_workdirs: Captured task working directories.
        work_dir: The Nextflow session work directory (string path).
        execution_report: Snapshot of execution stats.
    """

    def __init__(
        self,
        *,
        workflow_events: list[dict] | None = None,
        file_events: list[dict] | None = None,
        task_workdirs: list[str] | None = None,
        work_dir: str | None = None,
        execution_report: dict[str, Any] | None = None,
    ) -> None:
        self._workflow_events = workflow_events or []
        self._file_events = file_events or []
        self._task_workdirs = task_workdirs or []
        self._work_dir = work_dir
        self._execution_report = execution_report or {}

    def get_output_files(self) -> list[str]:
        """Return output file paths, preferring published metadata."""
        paths = _outputs.collect_paths_from_events(self._workflow_events, self._file_events)
        if not paths:
            paths = _outputs.collect_paths_from_workdirs(self._task_workdirs)
        return paths

    def get_workflow_outputs(self) -> list[dict[str, Any]]:
        """Return a structured representation of workflow outputs.

        Returns:
            List of dictionaries with ``name`` / ``value`` / ``index``.
        """
        outputs: list[dict[str, Any]] = []
        for event in self._workflow_events:
            if not isinstance(event, dict):
                continue
            outputs.append(
                {
                    "name": event.get("name"),
                    "value": to_python(event.get("value")),
                    "index": to_python(event.get("index")),
                }
            )
        return outputs

    def get_execution_report(self) -> dict[str, Any]:
        """Return execution statistics snapshotted during the run."""
        return dict(self._execution_report)

    def get_stdout(self) -> str:
        """Return the first available ``.command.out`` from captured workdirs.

        This is a best-effort helper that scans captured task work directories.
        """
        for workdir in self._task_workdirs:
            try:
                out_path = Path(workdir) / ".command.out"
                if out_path.exists():
                    return out_path.read_text()
            except Exception:
                continue
        return ""

    # Small introspection helpers for debugging / UX
    def workflow_events(self) -> list[dict]:
        return list(self._workflow_events)

    def file_events(self) -> list[dict]:
        return list(self._file_events)

    def task_workdirs(self) -> list[str]:
        return list(self._task_workdirs)
