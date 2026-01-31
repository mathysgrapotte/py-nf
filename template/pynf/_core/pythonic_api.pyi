from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChannelSpec:
    index: int
    param_names: tuple[str, ...]


class InputGroupingError(ValueError):
    """Raised when `**kwargs` cannot be mapped to input groups unambiguously."""


def channel_specs(input_channels: list[dict]) -> list[ChannelSpec]: ...


def auto_group_inputs(*, input_channels: list[dict], kwargs: dict[str, Any]) -> list[dict[str, Any]]: ...
