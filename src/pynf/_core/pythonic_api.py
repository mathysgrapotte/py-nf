"""Pythonic API helpers.

This module contains the logic for a "pythonic" call style:

```python
result = run_module("fastqc", reads=["R1.fq"], meta={"id": "s1"})
```

The core challenge is mapping ``**kwargs`` onto Nextflow input *channels*.
We solve this by:
- introspecting the module inputs via Nextflow native metadata
- assigning keyword arguments to channels by parameter name
- raising a detailed error when the mapping is ambiguous

This is intentionally a *constrained magic*: ambiguity is an error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ChannelSpec:
    """A simplified view of one Nextflow input channel."""

    index: int
    param_names: tuple[str, ...]


class InputGroupingError(ValueError):
    """Raised when ``**kwargs`` cannot be mapped to input groups unambiguously."""


def channel_specs(input_channels: list[dict]) -> list[ChannelSpec]:
    """Convert introspected input channels into lightweight channel specs."""
    specs: list[ChannelSpec] = []
    for i, ch in enumerate(input_channels):
        params = ch.get("params", [])
        names: list[str] = []
        if isinstance(params, list):
            for p in params:
                if isinstance(p, dict) and "name" in p:
                    names.append(str(p["name"]))
        specs.append(ChannelSpec(index=i, param_names=tuple(names)))
    return specs


def auto_group_inputs(*, input_channels: list[dict], kwargs: dict[str, Any]) -> list[dict[str, Any]]:
    """Infer input groups for a module from ``**kwargs``.

    Args:
        input_channels: Introspected channel definitions from Nextflow.
        kwargs: User-provided keyword arguments.

    Returns:
        List of input-group dictionaries, aligned to the channel order.

    Raises:
        InputGroupingError: if unknown inputs are provided or the assignment is ambiguous.
    """
    specs = channel_specs(input_channels)

    # Prepare empty groups (must match number of channels for validation).
    groups: list[dict[str, Any]] = [dict() for _ in specs]

    # Build index: param name -> channel indices that accept it.
    name_to_channels: dict[str, list[int]] = {}
    for spec in specs:
        for name in spec.param_names:
            name_to_channels.setdefault(name, []).append(spec.index)

    unknown = [k for k in kwargs.keys() if k not in name_to_channels]
    if unknown:
        raise InputGroupingError(
            "Unknown input parameter(s): "
            + ", ".join(sorted(unknown))
            + ". Expected one of: "
            + ", ".join(sorted(name_to_channels.keys()))
        )

    # Split into unambiguous and ambiguous keys.
    fixed: dict[str, int] = {}
    ambiguous: dict[str, list[int]] = {}
    for k in kwargs:
        candidates = name_to_channels[k]
        if len(candidates) == 1:
            fixed[k] = candidates[0]
        else:
            ambiguous[k] = candidates

    # Assign fixed keys.
    for k, idx in fixed.items():
        groups[idx][k] = kwargs[k]

    # Backtracking assign ambiguous keys.
    amb_keys = list(ambiguous.keys())

    def missing_for_group(i: int) -> set[str]:
        expected = set(specs[i].param_names)
        provided = set(groups[i].keys())
        return expected - provided

    def solve(pos: int) -> bool:
        if pos >= len(amb_keys):
            return True
        key = amb_keys[pos]
        candidates = ambiguous[key]

        # Heuristic: try channels that actually still need this key first.
        ordered = sorted(
            candidates,
            key=lambda i: (key not in missing_for_group(i), i),
        )

        for idx in ordered:
            if key in groups[idx]:
                continue
            groups[idx][key] = kwargs[key]
            if solve(pos + 1):
                return True
            del groups[idx][key]

        return False

    if ambiguous:
        ok = solve(0)
        if not ok:
            raise InputGroupingError(
                "Ambiguous input mapping. Some keyword arguments match multiple input channels. "
                "Please provide explicit grouped inputs (list of dicts) via ExecutionRequest.inputs. "
                f"Ambiguous keys: {sorted(ambiguous.keys())}"
            )

    # After assignment, ensure every channel is satisfied.
    missing_per_channel = []
    for spec in specs:
        missing = set(spec.param_names) - set(groups[spec.index].keys())
        if missing:
            missing_per_channel.append((spec.index, sorted(missing)))

    if missing_per_channel:
        lines = ["Missing required inputs:"]
        for idx, missing in missing_per_channel:
            lines.append(f"- input group {idx+1}: {', '.join(missing)}")
        raise InputGroupingError("\n".join(lines))

    return groups
