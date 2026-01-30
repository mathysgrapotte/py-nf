"""Validation helpers for module inputs and meta maps.

These functions keep validation logic pure and deterministic, making it easier
to test validation behavior in isolation from runtime orchestration."""

from __future__ import annotations

from typing import Any

def validate_meta_map(
    meta: Mapping[str, Any], required_fields: Sequence[str] | None = None
) -> None:
    """Validate that required fields exist in a meta mapping.

Args:
    meta: Metadata mapping supplied by the user.
    required_fields: Optional list of required keys. Defaults to ``["id"]``.

Raises:
    ValueError: If any required fields are missing.

Example:
    >>> validate_meta_map({"id": "sample1"}, ["id"])"""
    ...

def normalize_inputs(
    inputs: Sequence[Mapping[str, Any]] | None,
) -> list[Mapping[str, Any]]:
    """Normalize optional inputs into a concrete list.

Args:
    inputs: Optional sequence of input-group mappings.

Returns:
    A list of input-group mappings, or an empty list when ``inputs`` is
    ``None``.

Example:
    >>> normalize_inputs(None)
    []"""
    ...

def validate_inputs(inputs, input_channels) -> None:
    """Validate user-provided inputs against expected input channels.

Args:
    inputs: Input group mappings supplied by the user.
    input_channels: Expected channel specifications extracted from a
        Nextflow script.

Raises:
    ValueError: If inputs are missing, extra, or structurally incorrect.

Example:
    >>> validate_inputs([{"reads": "sample.fq"}], [{'type': 'tuple', 'params': [{'name': 'reads', 'type': 'path'}]}])"""
    ...

