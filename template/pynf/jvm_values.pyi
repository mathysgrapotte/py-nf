"""JPype value conversions."""

from __future__ import annotations

from typing import Any


def to_java(value: Any, *, param_type: str | None = ...) -> Any: ...

def to_python(value: Any) -> Any: ...
