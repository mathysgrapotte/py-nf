"""Pure output extraction and normalization utilities."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import jpype


def flatten_paths(value: Any) -> Iterator[str]:
    """Yield file paths from nested Java or Python structures.

    Args:
        value: Arbitrary value containing path-like objects.

    Yields:
        String file paths extracted from nested structures.
    """

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
    """Collect unique paths from workflow and file publish events.

    Args:
        workflow_events: Workflow output events from the observer.
        file_events: File publish events from the observer.

    Returns:
        Ordered list of unique file paths.
    """
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
    """Collect visible files from task work directories.

    Args:
        task_workdirs: Work directory paths captured during execution.

    Returns:
        Ordered list of unique file paths.
    """
    outputs: list[str] = []
    seen: set[str] = set()
    for workdir in task_workdirs:
        extend_unique(outputs, seen, _iter_visible_files(workdir))
    return outputs


def extend_unique(
    result_list: list[str], seen: set[str], values: Iterable[str]
) -> None:
    """Append unseen values while preserving order.

    Args:
        result_list: List to append values to.
        seen: Set tracking already-seen values.
        values: Iterable of candidate values.
    """
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result_list.append(value)


def _iter_visible_files(workdir: str) -> Iterator[str]:
    """Yield non-hidden files within a work directory.

    Args:
        workdir: Work directory path.

    Yields:
        Absolute file paths for non-hidden files.
    """
    workdir_path = Path(workdir)
    if not workdir_path.exists():
        return
    for file in workdir_path.iterdir():
        if file.is_file() and not file.name.startswith("."):
            yield str(file.absolute())


def _is_java_path_like(obj: Any) -> bool:
    """Return ``True`` when the object is a Java path or file.

    Args:
        obj: Candidate object.

    Returns:
        ``True`` if the object looks like a Java path or file.
    """
    java_path = jpype.JClass("java.nio.file.Path")
    if isinstance(obj, java_path):
        return True

    java_file = jpype.JClass("java.io.File")
    if isinstance(obj, java_file):
        return True

    return False
