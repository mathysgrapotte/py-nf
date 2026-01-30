"""Result objects returned from Nextflow execution.

This module is deliberately self-contained:
- it provides the stable :class:`~pynf._core.result.NextflowResult`
- it contains the "extract output file paths" logic
- it contains best-effort Java→Python normalization for workflow outputs

The goal is to keep the public runtime surface small and easy to reason about."""

from __future__ import annotations

from typing import Any

def to_python(value: Any) -> Any:
    """Convert a Java/JPype object into JSON-ish Python values.

This is used for turning Nextflow workflow outputs into plain values.

Args:
    value: Java or Python value.

Returns:
    A Python-serializable value (or string fallback)."""
    ...

class NextflowResult:
    """A stable, event-based result for a single Nextflow execution.

This object intentionally avoids holding on to live JVM objects. All the data
it exposes is captured (snapshotted) during execution."""
    ...

def flatten_paths(value: Any) -> Iterator[str]:
    """Yield normalized filesystem paths from nested Java/Python structures."""
    ...

def collect_paths_from_events(
    workflow_events: Sequence[dict], file_events: Sequence[dict]
) -> list[str]:
    """Collect unique paths from workflow and file publish events."""
    ...

def collect_paths_from_workdirs(task_workdirs: Sequence[str]) -> list[str]:
    """Collect visible files from task work directories."""
    ...

def extend_unique(result_list: list[str], seen: set[str], values: Iterable[str]) -> None:
    ...

