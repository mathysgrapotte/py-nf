"""Pure output extraction and normalization utilities."""

from typing import Any, Iterable, Iterator, Sequence

def flatten_paths(value: Any) -> Iterator[str]:
    """Yield string paths extracted from nested values.

    DEPENDS_ON:
    pynf.outputs._is_java_path_like

    EXTERNAL_DEPENDS_ON:
    jpype
    pathlib
    """
    ...

def collect_paths_from_events(
    workflow_events: Sequence[dict], file_events: Sequence[dict]
) -> list[str]:
    """Collect unique paths from observer events.

    DEPENDS_ON:
    pynf.outputs.flatten_paths
    pynf.outputs.extend_unique

    EXTERNAL_DEPENDS_ON:
    None
    """
    ...

def collect_paths_from_workdirs(task_workdirs: Sequence[str]) -> list[str]:
    """Fallback: collect files from task work directories.

    DEPENDS_ON:
    pynf.outputs._iter_visible_files

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def extend_unique(
    result_list: list[str], seen: set[str], values: Iterable[str]
) -> None:
    """Append unseen values while preserving order.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    typing
    """
    ...

def _iter_visible_files(workdir: str) -> Iterator[str]:
    """Yield visible files in a work directory.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    pathlib
    """
    ...

def _is_java_path_like(obj: Any) -> bool:
    """Return True when the object looks like a Java path or file.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    jpype
    """
    ...
