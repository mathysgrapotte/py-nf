"""Validation helpers (stubs)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def validate_meta_map(meta: Mapping[str, Any], required_fields: Sequence[str] | None = ...) -> None: ...

def normalize_inputs(inputs: Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]: ...

def validate_inputs(inputs: Any, input_channels: Any) -> None: ...
