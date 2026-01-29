"""Rendering helpers for CLI output."""

from typing import Mapping, Sequence

from rich.table import Table

def input_group_table(group_idx: int, input_group: Mapping[str, object]) -> Table:
    """Render a rich table showcasing a single module input channel.

    Provides column headers for parameter names and types so the CLI can prettify
    module input metadata.

    Example:
        >>> input_group_table(0, {"type": "tuple", "params": [{"name": "reads", "type": "path"}]})
        Table(title='Input Channel 1 (type: tuple)', ...)

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    rich.table
    """
    ...

def modules_table(modules: Sequence[str], limit: int | None = None) -> Table:
    """Render a modules table with optional truncation.

    Displays module names alongside a heuristic-based type (top-level vs submodule)
    so users can quickly scan available tools.

    Example:
        >>> modules_table(["samtools", "samtools/view"], limit=2)
        Table(title='Available nf-core Modules', ...)

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    rich.table
    """
    ...
