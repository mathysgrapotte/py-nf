"""Validation helpers for module inputs and meta maps.

These functions keep validation logic pure and deterministic, making it easier
to test validation behavior in isolation from runtime orchestration.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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
        >>> validate_meta_map({"id": "sample1"}, ["id"])
    """
    required = list(required_fields) if required_fields is not None else ["id"]
    missing = [field for field in required if field not in meta]
    if missing:
        raise ValueError(
            "Missing required meta fields: "
            f"{', '.join(missing)}. Meta map provided: {dict(meta)}"
        )


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
        []
    """
    return [] if inputs is None else list(inputs)


def validate_inputs(inputs, input_channels) -> None:
    """Validate user-provided inputs against expected input channels.

    Args:
        inputs: Input group mappings supplied by the user.
        input_channels: Expected channel specifications extracted from a
            Nextflow script.

    Raises:
        ValueError: If inputs are missing, extra, or structurally incorrect.

    Example:
        >>> validate_inputs([{"reads": "sample.fq"}], [{'type': 'tuple', 'params': [{'name': 'reads', 'type': 'path'}]}])
    """
    if not input_channels:
        if inputs:
            raise ValueError("Module has no inputs, but inputs were provided")
        return

    normalized_inputs = normalize_inputs(inputs)
    _validate_input_count(normalized_inputs, input_channels)

    for idx, (user_input, expected_channel) in enumerate(
        zip(normalized_inputs, input_channels)
    ):
        _validate_input_group(user_input, expected_channel, idx)


def _validate_input_count(inputs, input_channels) -> None:
    """Validate that the number of input groups matches expectations.

    Args:
        inputs: Normalized list of input group mappings.
        input_channels: Expected channel specifications.

    Raises:
        ValueError: If the number of input groups does not match.

    Example:
        >>> _validate_input_count([{}], [{'type': 'tuple', 'params': []}])
    """
    if len(inputs) != len(input_channels):
        raise ValueError(_format_count_error(inputs, input_channels))


def _validate_input_group(user_input, expected_channel, group_idx: int) -> None:
    """Validate a single input group against a channel definition.

    Args:
        user_input: Mapping for the current input group.
        expected_channel: Channel metadata extracted from the script.
        group_idx: Zero-based group index used for error messages.

    Raises:
        ValueError: If required parameters are missing or extra parameters exist.

    Example:
        >>> _validate_input_group({'reads': 'a.fq'}, expected_channel, 0)
    """
    channel_type = expected_channel.get("type")
    expected_params = expected_channel.get("params", [])

    expected_param_names = {p["name"] for p in expected_params}
    user_param_names = set(user_input.keys())

    missing_params = expected_param_names - user_param_names
    if missing_params:
        raise ValueError(
            _format_missing_params_error(
                missing_params, expected_params, group_idx, channel_type
            )
        )

    extra_params = user_param_names - expected_param_names
    if extra_params:
        raise ValueError(
            _format_extra_params_error(
                extra_params, expected_params, group_idx, channel_type
            )
        )


def _format_count_error(inputs, input_channels) -> str:
    """Format a detailed error for mismatched input counts.

    Args:
        inputs: Normalized list of input group mappings.
        input_channels: Expected channel specifications.

    Returns:
        Human-readable multi-line error message.

    Example:
        >>> _format_count_error([], [{'type': 'tuple', 'params': []}])
    """
    count = len(inputs) if inputs else 0
    lines = [
        "",
        "=" * 70,
        "ERROR: Incorrect number of input groups",
        "=" * 70,
        "",
        f"Expected {len(input_channels)} input group(s), but got {count}",
        "",
        "Expected input structure:",
        _format_expected_structure(input_channels).rstrip("\n"),
    ]

    if inputs:
        lines.extend(
            ["", "Provided inputs:", _format_provided_inputs(inputs).rstrip("\n")]
        )

    lines.extend(["", "=" * 70, ""])
    return "\n".join(lines)


def _format_missing_params_error(
    missing_params, expected_params, group_idx, channel_type
) -> str:
    """Format a detailed error when required parameters are missing.

    Args:
        missing_params: Set of missing parameter names.
        expected_params: Expected parameter definitions.
        group_idx: Zero-based group index.
        channel_type: Expected channel type string.

    Returns:
        Human-readable multi-line error message.

    Example:
        >>> _format_missing_params_error({'reads'}, expected_params, 0, 'tuple')
    """
    group_number = group_idx + 1
    lines = [
        "",
        "=" * 70,
        f"ERROR: Missing required parameters in input group {group_number}",
        "=" * 70,
        "",
        f"Missing parameters: {', '.join(sorted(missing_params))}",
        "",
        f"Input group {group_number} expects (type: {channel_type}):",
    ]
    lines.extend(f"  - {param['type']}({param['name']})" for param in expected_params)
    lines.extend(["", "=" * 70, ""])
    return "\n".join(lines)


def _format_extra_params_error(
    extra_params, expected_params, group_idx, channel_type
) -> str:
    """Format a detailed error when extra parameters are provided.

    Args:
        extra_params: Set of unexpected parameter names.
        expected_params: Expected parameter definitions.
        group_idx: Zero-based group index.
        channel_type: Expected channel type string.

    Returns:
        Human-readable multi-line error message.

    Example:
        >>> _format_extra_params_error({'foo'}, expected_params, 0, 'tuple')
    """
    group_number = group_idx + 1
    lines = [
        "",
        "=" * 70,
        f"ERROR: Unexpected parameters in input group {group_number}",
        "=" * 70,
        "",
        f"Unexpected parameters: {', '.join(sorted(extra_params))}",
        "",
        f"Input group {group_number} expects (type: {channel_type}):",
    ]
    lines.extend(f"  - {param['type']}({param['name']})" for param in expected_params)
    lines.extend(["", "=" * 70, ""])
    return "\n".join(lines)


def _format_expected_structure(input_channels) -> str:
    """Render the expected input structure for diagnostics.

    Args:
        input_channels: Expected channel specifications.

    Returns:
        Formatted input structure string.

    Example:
        >>> _format_expected_structure([{'type': 'tuple', 'params': [{'name': 'reads', 'type': 'path'}]}])
    """
    lines = ["inputs=["]
    for idx, channel in enumerate(input_channels):
        channel_type = channel.get("type")
        params = channel.get("params", [])
        lines.append(f"    # Group {idx + 1} (type: {channel_type})")
        param_strs = [f"'{p['name']}': <value>" for p in params]
        lines.append(f"    {{{', '.join(param_strs)}}},")
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def _format_provided_inputs(inputs) -> str:
    """Render provided inputs for diagnostics.

    Args:
        inputs: List of user-provided input group mappings.

    Returns:
        Formatted input structure string.

    Example:
        >>> _format_provided_inputs([{'reads': 'sample.fq'}])
    """
    lines = ["inputs=["]
    for idx, inp in enumerate(inputs):
        lines.append(f"    # Group {idx + 1}")
        lines.append(f"    {inp},")
    lines.append("]")
    lines.append("")
    return "\n".join(lines)
