"""Rendering helpers for CLI output."""

from typing import Mapping, Sequence

from rich.table import Table

def input_group_table(group_idx: int, input_group: Mapping[str, object]) -> Table:
    """Render a rich table for a module input group.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    rich.table
    """
    ...

def modules_table(modules: Sequence[str], limit: int | None = None) -> Table:
    """Render a modules table with optional truncation.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    rich.table
    """
    ...
