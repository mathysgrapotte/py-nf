"""Pythonic API helpers.

We want a call style like:

```python
pynf.run_module("fastqc", reads=["R1.fq"], meta={"id": "s1"})
```

The tricky part is mapping `**kwargs` onto Nextflow *input channels*.

Readability-first rule:
- We only support mappings that are **obviously unambiguous**.
- If an input name could belong to more than one channel, we raise and ask the
  caller to provide explicit grouped inputs (via `ExecutionRequest.inputs`).

This keeps the behavior explicit and avoids surprising heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChannelSpec:
    """A simplified view of one Nextflow input channel."""

    index: int
    param_names: tuple[str, ...]


class InputGroupingError(ValueError):
    """Raised when `**kwargs` cannot be mapped to input groups unambiguously."""


def channel_specs(input_channels: list[dict]) -> list[ChannelSpec]:
    """Convert introspected input channels into lightweight channel specs."""
    specs: list[ChannelSpec] = []

    for index, channel in enumerate(input_channels):
        params = channel.get("params", [])
        names: list[str] = []

        if isinstance(params, list):
            for param in params:
                if isinstance(param, dict) and "name" in param:
                    names.append(str(param["name"]))

        specs.append(ChannelSpec(index=index, param_names=tuple(names)))

    return specs


def auto_group_inputs(*, input_channels: list[dict], kwargs: dict[str, Any]) -> list[dict[str, Any]]:
    """Infer input groups for a module from `**kwargs`.

    Returns the list-of-dicts representation expected by `ExecutionRequest.inputs`,
    aligned to the module input channel order.

    Strict rules:
    - Unknown keyword names are an error.
    - If any keyword name matches multiple channels, we raise (no guessing).
    - All channels must be fully satisfied (all expected param names present).
    """
    specs = channel_specs(input_channels)
    groups: list[dict[str, Any]] = [dict() for _ in specs]

    # Index: param name -> channel index.
    # If a param name exists in multiple channels, we treat that as ambiguous.
    name_to_channel: dict[str, int] = {}
    ambiguous_names: set[str] = set()

    for spec in specs:
        for name in spec.param_names:
            if name in name_to_channel:
                ambiguous_names.add(name)
            else:
                name_to_channel[name] = spec.index

    if ambiguous_names:
        raise InputGroupingError(
            "Ambiguous module input schema: these names appear in multiple channels: "
            + ", ".join(sorted(ambiguous_names))
            + ". Use explicit grouped inputs via ExecutionRequest.inputs."
        )

    unknown = [key for key in kwargs.keys() if key not in name_to_channel]
    if unknown:
        raise InputGroupingError(
            "Unknown input parameter(s): "
            + ", ".join(sorted(unknown))
            + ". Expected one of: "
            + ", ".join(sorted(name_to_channel.keys()))
        )

    for key, value in kwargs.items():
        group_index = name_to_channel[key]
        groups[group_index][key] = value

    missing_lines: list[str] = []
    for spec in specs:
        missing = [name for name in spec.param_names if name not in groups[spec.index]]
        if missing:
            missing_lines.append(f"- input group {spec.index + 1}: {', '.join(missing)}")

    if missing_lines:
        raise InputGroupingError("Missing required inputs:\n" + "\n".join(missing_lines))

    return groups
