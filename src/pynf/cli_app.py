"""CLI application wiring for pynf."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CLIContext:
    """Shared CLI configuration for Click commands.

    Attributes:
        cache_dir: Optional directory for cached module artifacts.
        github_token: Optional GitHub token for authenticated requests.

    Example:
        >>> CLIContext(cache_dir=Path("~/.cache/nf-core-modules"))
        CLIContext(cache_dir=PosixPath('~/.cache/nf-core-modules'), github_token=None)
    """

    cache_dir: Path | None = None
    github_token: str | None = None


def build_cli() -> object:
    """Construct and return the Click CLI application.

    Returns:
        Click command group instance initialized with pynf commands and helpers.

    Example:
        >>> cli_group = build_cli()
        >>> isinstance(cli_group, click.core.Group)
        True
    """
    from .cli import cli

    return cli


def main() -> None:
    """Invoke the pynf CLI entry point.

    Example:
        >>> # Usually triggered via console_scripts entry point
        >>> main()
        # On success the CLI will exit with a zero status code.
    """
    build_cli()()
