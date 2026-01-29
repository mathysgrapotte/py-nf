"""JPype value conversions.

Central place for converting:
- Python values → Java-friendly values (for input params)
- Java/JPype values → JSON-ish Python values (for results/reporting)

Keeping this in one module prevents subtle drift between:
- execution input conversion
- workflow output serialization
- output file path extraction
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, cast

import jpype


def to_java(value: Any, *, param_type: str | None = None) -> Any:
    """Convert a Python value to something Nextflow/Java code can consume.

    Args:
        value: Python value.
        param_type: Optional Nextflow parameter type (e.g. ``path``).

    Returns:
        A Java-compatible value.

    Notes:
        - ``Path`` values are passed as strings.
        - dict-like values are converted to ``java.util.HashMap``.
        - list-like values are converted to ``java.util.ArrayList``.

    Example:
        >>> to_java({"id": "sample1"})  # doctest: +SKIP
        <java.util.HashMap ...>
    """
    if value is None:
        return None

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Mapping):
        HashMap = jpype.JClass("java.util.HashMap")
        m = HashMap()
        for k, v in value.items():
            m.put(str(k), to_java(v))
        return m

    if isinstance(value, (list, tuple, set)):
        ArrayList = jpype.JClass("java.util.ArrayList")
        arr = ArrayList()
        for item in value:
            arr.add(to_java(item, param_type=param_type))
        return arr

    # Fallback: best effort
    return value


def to_python(value: Any) -> Any:
    """Convert a Java/JPype object into JSON-ish Python values.

    This is used for turning Nextflow workflow outputs into plain values.

    Args:
        value: Java or Python value.

    Returns:
        A Python-serializable value (or string fallback).

    Example:
        >>> to_python(123)
        123
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    # Java Map-like (including HashMap)
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
