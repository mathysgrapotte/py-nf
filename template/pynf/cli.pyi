"""Click CLI for managing nf-core modules and Nextflow scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import click


@dataclass
class CLIContext:
    cache_dir: Path | None = ...
    github_token: str | None = ...


def cli(ctx: click.Context, cache_dir: Optional[str], github_token: Optional[str]) -> None: ...

def list_modules_cmd(ctx: CLIContext, limit: Optional[int], rate_limit: bool) -> None: ...

def list_submodules(ctx: CLIContext, module: str) -> None: ...

def download(ctx: CLIContext, module: str, force: bool) -> None: ...

def list_inputs(ctx: CLIContext, module: str, output_json: bool) -> None: ...

def inspect(ctx: CLIContext, module: str, output_json: bool) -> None: ...

def run(
    ctx: CLIContext,
    module: str,
    inputs: Optional[str],
    params: Optional[str],
    docker: bool,
    executor: str,
    verbose: bool,
) -> None: ...

def main() -> None: ...
