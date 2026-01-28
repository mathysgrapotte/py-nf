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
    """

    cache_dir: Path | None = None
    github_token: str | None = None


def build_cli() -> object:
    """Construct and return the Click CLI application.

    Returns:
        Click command group instance.
    """
    from .cli import cli

    return cli


def main() -> None:
    """CLI entry point."""
    build_cli()()
