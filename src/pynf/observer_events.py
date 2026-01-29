"""Observer adapters that collect Nextflow execution events."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowOutputCollector:
    """Collect workflow outputs, file publish events, and task workdirs.

    This class is designed to be passed into a JPype proxy for Nextflow's
    ``TraceObserverV2`` interface.
    """

    def __init__(self) -> None:
        self._workflow_events: list[dict] = []
        self._file_events: list[dict] = []
        self._task_workdirs: list[str] = []

    def onFlowCreate(self, session: Any) -> None:  # noqa: D401 - required signature
        return None

    def onFlowBegin(self) -> None:
        return None

    def onFlowComplete(self) -> None:
        return None

    def onProcessCreate(self, process: Any) -> None:
        return None

    def onProcessTerminate(self, process: Any) -> None:
        return None

    def onTaskPending(self, event: Any) -> None:
        return None

    def onTaskSubmit(self, event: Any) -> None:
        return None

    def onTaskStart(self, event: Any) -> None:
        return None

    def onTaskComplete(self, event: Any) -> None:
        self._record_task_workdir(event, "onTaskComplete")

    def onTaskCached(self, event: Any) -> None:
        self._record_task_workdir(event, "onTaskCached")

    def onFlowError(self, event: Any) -> None:
        return None

    def onWorkflowOutput(self, event: Any) -> None:
        self._workflow_events.append(
            {
                "name": event.getName(),
                "value": event.getValue(),
                "index": event.getIndex(),
            }
        )

    def onFilePublish(self, event: Any) -> None:
        self._file_events.append(
            {
                "target": event.getTarget(),
                "source": event.getSource(),
                "labels": event.getLabels(),
            }
        )

    def workflow_events(self) -> list[dict]:
        """Return collected workflow output events."""
        return list(self._workflow_events)

    def file_events(self) -> list[dict]:
        """Return collected file publish events."""
        return list(self._file_events)

    def task_workdirs(self) -> list[str]:
        """Return the list of task work directories."""
        return list(self._task_workdirs)

    def _record_task_workdir(self, event: Any, hook_name: str) -> None:
        """Record the work directory from a task callback.

        Args:
            event: Nextflow event containing task metadata.
            hook_name: Name of the event callback for logging.
        """
        logger.debug("%s called", hook_name)
        handler = event.getHandler()
        task = handler.getTask()
        workdir = str(task.getWorkDir())
        logger.debug("Task workDir: %s", workdir)
        self._task_workdirs.append(workdir)
