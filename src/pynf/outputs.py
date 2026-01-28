"""Pure output extraction and normalization utilities."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any

import jpype


def flatten_paths(value: Any) -> Iterator[str]:
    """Yield string paths extracted from nested Java/Python structures."""

    def visit(obj: Any) -> Iterator[str]:
        if obj is None:
            return

        if isinstance(obj, str):
            if obj:
                yield obj
            return

        if _is_java_path_like(obj):
            try:
                yield str(obj.toAbsolutePath())
            except Exception:
                try:
                    yield str(obj.toPath())
                except Exception:
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

        if jpype.isJArray(obj):
            for item in obj:
                yield from visit(item)
            return

        if hasattr(obj, "entrySet") and callable(obj.entrySet):
            for entry in obj.entrySet():
                yield from visit(entry.getValue())
            return

        if hasattr(obj, "iterator"):
            iterator = obj.iterator()
            while iterator.hasNext():
                yield from visit(iterator.next())
            return

        try:
            for item in obj:
                yield from visit(item)
            return
        except TypeError:
            pass

        if hasattr(obj, "getValue") and callable(obj.getValue):
            yield from visit(obj.getValue())

    yield from visit(value)


def collect_paths_from_events(workflow_events: Sequence[dict], file_events: Sequence[dict]) -> list[str]:
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
    """Fallback: collect visible files from task work directories."""
    outputs: list[str] = []
    seen: set[str] = set()
    for workdir in task_workdirs:
        extend_unique(outputs, seen, _iter_visible_files(workdir))
    return outputs


def extend_unique(result_list: list[str], seen: set[str], values: Iterable[str]) -> None:
    """Append unseen values while preserving order."""
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result_list.append(value)


def _iter_visible_files(workdir: str) -> Iterator[str]:
    """Yield non-hidden files within a work directory."""
    workdir_path = Path(workdir)
    if not workdir_path.exists():
        return
    for file in workdir_path.iterdir():
        if file.is_file() and not file.name.startswith("."):
            yield str(file.absolute())


def _is_java_path_like(obj: Any) -> bool:
    """Return True when the object is a Java path or file."""
    try:
        java_path = jpype.JClass("java.nio.file.Path")
        if isinstance(obj, java_path):
            return True
    except RuntimeError:
        pass

    try:
        java_file = jpype.JClass("java.io.File")
        if isinstance(obj, java_file):
            return True
    except RuntimeError:
        pass

    return False
