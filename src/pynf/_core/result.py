"""Result objects returned from Nextflow execution.

This module is deliberately self-contained:
- it provides the stable :class:`~pynf._core.result.NextflowResult`
- it contains the "extract output file paths" logic
- it contains best-effort Java→Python normalization for workflow outputs

The goal is to keep the public runtime surface small and easy to reason about.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import jpype


def to_python(value: Any) -> Any:
    """Convert a Java/JPype object into JSON-ish Python values.

    This is used for turning Nextflow workflow outputs into plain values.

    Args:
        value: Java or Python value.

    Returns:
        A Python-serializable value (or string fallback).
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    # Java Map-like
    if hasattr(value, "entrySet") and callable(value.entrySet):
        out: dict[Any, Any] = {}
        entry_set = value.entrySet()
        iterator = entry_set.iterator()
        while iterator.hasNext():  # type: ignore[attr-defined]
            entry = iterator.next()  # type: ignore[attr-defined]
            out[to_python(entry.getKey())] = to_python(entry.getValue())
        return out

    # Java Iterable / Iterator
    iterator_factory = getattr(value, "iterator", None)
    if callable(iterator_factory):
        iterator = iterator_factory()
        out_list: list[Any] = []
        while iterator.hasNext():  # type: ignore[attr-defined]
            out_list.append(to_python(iterator.next()))  # type: ignore[attr-defined]
        return out_list

    if isinstance(value, Iterable):
        return [to_python(v) for v in cast(Iterable[Any], value)]

    return str(value)


class NextflowResult:
    """A stable, event-based result for a single Nextflow execution.

    This object intentionally avoids holding on to live JVM objects. All the data
    it exposes is captured (snapshotted) during execution.
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
        paths = collect_paths_from_events(self._workflow_events, self._file_events)
        if not paths:
            paths = collect_paths_from_workdirs(self._task_workdirs)
        return paths

    def get_workflow_outputs(self) -> list[dict[str, Any]]:
        """Return workflow outputs as JSON-ish Python structures."""
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
        """Return the first available ``.command.out`` from captured workdirs."""
        for workdir in self._task_workdirs:
            try:
                out_path = Path(workdir) / ".command.out"
                if out_path.exists():
                    return out_path.read_text()
            except Exception:
                continue
        return ""

    def workflow_events(self) -> list[dict]:
        return list(self._workflow_events)

    def file_events(self) -> list[dict]:
        return list(self._file_events)

    def task_workdirs(self) -> list[str]:
        return list(self._task_workdirs)


class SeqeraResult:
    """Result summary for a remote Seqera Platform execution.

    This object exposes a minimal, stable surface for remote runs.
    """

    def __init__(
        self,
        *,
        workflow_id: str,
        status: str,
        execution_report: dict[str, Any] | None = None,
        outdir: str | None = None,
        url: str | None = None,
    ) -> None:
        self._workflow_id = workflow_id
        self._status = status
        self._execution_report = execution_report or {}
        self._outdir = outdir
        self._url = url

    @property
    def workflow_id(self) -> str:
        return self._workflow_id

    @property
    def url(self) -> str | None:
        return self._url

    def get_execution_report(self) -> dict[str, Any]:
        report = dict(self._execution_report)
        report.setdefault("workflow_id", self._workflow_id)
        report.setdefault("status", self._status)
        if self._url:
            report.setdefault("url", self._url)
        if self._outdir:
            report.setdefault("outdir", self._outdir)
        return report

    def get_output_files(self) -> list[str]:
        if not self._outdir:
            return []
        return [self._outdir]


def flatten_paths(value: Any) -> Iterator[str]:
    """Yield normalized filesystem paths from nested Java/Python structures."""

    def visit(obj: Any) -> Iterator[str]:
        if obj is None:
            return

        if isinstance(obj, str):
            if obj:
                yield obj
            return

        if _is_java_path_like(obj):
            if hasattr(obj, "toAbsolutePath"):
                yield str(obj.toAbsolutePath())
            elif hasattr(obj, "toPath"):
                yield str(obj.toPath())
            else:
                yield str(obj)
            return

        if isinstance(obj, Path):
            yield str(obj)
            return

        if isinstance(obj, dict):
            for item in obj.values():
                yield from visit(item)
            return

        if isinstance(obj, (list, tuple, set)):
            for item in obj:
                yield from visit(item)
            return

        if jpype.isJArray(obj):  # type: ignore[attr-defined]
            for item in cast(Iterable[Any], obj):
                yield from visit(item)
            return

        if hasattr(obj, "entrySet") and callable(obj.entrySet):
            entry_set = obj.entrySet()
            iterator_factory = getattr(entry_set, "iterator", None)
            if callable(iterator_factory):
                iterator = cast(Any, iterator_factory())
                while iterator.hasNext():  # type: ignore[attr-defined]
                    entry = iterator.next()  # type: ignore[attr-defined]
                    yield from visit(entry.getValue())
            return

        iterator_factory = getattr(obj, "iterator", None)
        if callable(iterator_factory):
            iterator = cast(Any, iterator_factory())
            while iterator.hasNext():  # type: ignore[attr-defined]
                yield from visit(iterator.next())  # type: ignore[attr-defined]
            return

        if isinstance(obj, Iterable):
            for item in cast(Iterable[Any], obj):
                yield from visit(item)
            return

        if hasattr(obj, "getValue") and callable(obj.getValue):
            yield from visit(obj.getValue())

    yield from visit(value)


def collect_paths_from_events(
    workflow_events: Sequence[dict], file_events: Sequence[dict]
) -> list[str]:
    """Collect unique paths from workflow and file publish events."""
    seen: set[str] = set()
    result: list[str] = []

    for event in workflow_events:
        if not isinstance(event, dict):
            continue
        extend_unique(result, seen, flatten_paths(event.get("value")))
        extend_unique(result, seen, flatten_paths(event.get("index")))

    for event in file_events:
        if not isinstance(event, dict):
            continue
        extend_unique(result, seen, flatten_paths(event.get("target")))

    return result


def collect_paths_from_workdirs(task_workdirs: Sequence[str]) -> list[str]:
    """Collect visible files from task work directories."""
    outputs: list[str] = []
    seen: set[str] = set()
    for workdir in task_workdirs:
        extend_unique(outputs, seen, _iter_visible_files(workdir))
    return outputs


def extend_unique(
    result_list: list[str], seen: set[str], values: Iterable[str]
) -> None:
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result_list.append(value)


def _iter_visible_files(workdir: str) -> Iterator[str]:
    workdir_path = Path(workdir)
    if not workdir_path.exists():
        return
    for file in workdir_path.iterdir():
        if file.is_file() and not file.name.startswith("."):
            yield str(file.absolute())


def _is_java_path_like(obj: Any) -> bool:
    if not jpype.isJVMStarted():  # type: ignore[attr-defined]
        return False

    java_path = jpype.JClass("java.nio.file.Path")
    if isinstance(obj, java_path):
        return True

    java_file = jpype.JClass("java.io.File")
    if isinstance(obj, java_file):
        return True

    return False
