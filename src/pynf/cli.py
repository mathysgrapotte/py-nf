"""
CLI for py-nf module management using Click and Rich.

Provides user-facing commands for listing, downloading, inspecting and running nf-core modules.
"""

import click
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from datetime import datetime

from . import tools

# Create a rich console for pretty printing
console = Console()


def _format_input_group_table(group_idx: int, input_group) -> Table:
    """
    Create a table for an input channel from native API format.

    Input format: {'type': 'tuple', 'params': [{'type': 'val', 'name': 'meta'}, ...]}
    """
    channel_type = input_group.get('type', 'unknown')
    params = input_group.get('params', [])

    table = Table(
        title=f"Input Channel {group_idx + 1} (type: {channel_type})",
        show_header=True,
        header_style="bold blue"
    )
    table.add_column("Parameter Name", style="cyan")
    table.add_column("Parameter Type", style="yellow")

    for param in params:
        param_name = param.get('name', 'unknown')
        param_type = param.get('type', 'unknown')
        table.add_row(param_name, param_type)

    return table


class CLIContext:
    """Context object for CLI commands."""

    def __init__(self, cache_dir: Optional[Path] = None, github_token: Optional[str] = None):
        self.cache_dir = cache_dir
        self.github_token = github_token


pass_context = click.make_pass_decorator(CLIContext)


@click.group()
@click.option(
    "--cache-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default=None,
    help="Directory to cache modules. Defaults to ./nf-core-modules",
)
@click.option(
    "--github-token",
    envvar="GITHUB_TOKEN",
    default=None,
    help="GitHub personal access token for higher rate limits.",
)
@click.pass_context
def cli(ctx, cache_dir: Optional[str], github_token: Optional[str]):
    """Nextflow workflow and nf-core module management CLI."""
    cache_path = Path(cache_dir) if cache_dir else None
    ctx.obj = CLIContext(cache_dir=cache_path, github_token=github_token)


@cli.command()
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit output to N modules.",
)
@click.option(
    "--rate-limit",
    is_flag=True,
    help="Show GitHub API rate limit status.",
)
@pass_context
def list_modules_cmd(ctx: CLIContext, limit: Optional[int], rate_limit: bool):
    """List all available nf-core modules."""
    try:
        with console.status("[bold green]Fetching modules..."):
            modules = tools.list_modules(cache_dir=ctx.cache_dir, github_token=ctx.github_token)

        if not modules:
            console.print("[yellow]No modules found.[/yellow]")
            return

        # Create and display table
        table = Table(title="Available nf-core Modules", show_header=True, header_style="bold magenta")
        table.add_column("Module Name", style="cyan")
        table.add_column("Type", style="green")

        display_modules = modules[:limit] if limit else modules

        for module in display_modules:
            # Simple heuristic: modules with '/' are likely submodules of a larger tool
            module_type = "sub-module" if "/" in module else "top-level"
            table.add_row(module, module_type)

        console.print(table)

        # Show count
        total = len(modules)
        shown = len(display_modules)
        if limit and shown < total:
            console.print(f"\n[yellow]Showing {shown}/{total} modules (use --limit to see more)[/yellow]")
        else:
            console.print(f"\n[green]Total: {total} modules[/green]")

        # Show rate limit if requested
        if rate_limit:
            try:
                status = tools.get_rate_limit_status(github_token=ctx.github_token)
                rate_table = Table(title="GitHub API Rate Limit", show_header=True, header_style="bold blue")
                rate_table.add_column("Metric", style="cyan")
                rate_table.add_column("Value", style="green")
                rate_table.add_row("Limit", str(status["limit"]))
                rate_table.add_row("Remaining", str(status["remaining"]))
                reset_time = datetime.fromtimestamp(status["reset_time"]).strftime("%Y-%m-%d %H:%M:%S")
                rate_table.add_row("Reset Time", reset_time)
                console.print(rate_table)
            except Exception as e:
                console.print(f"[red]Error fetching rate limit: {e}[/red]")

    except Exception as e:
        console.print(f"[red]Error listing modules: {e}[/red]", style="bold")
        raise click.Abort()


@cli.command("list-submodules")
@click.argument("module")
@pass_context
def list_submodules(ctx: CLIContext, module: str):
    """List submodules available in a module.

    Example: pynf list-submodules samtools
    """
    try:
        with console.status(f"[bold green]Fetching submodules for '{module}'..."):
            submodules = tools.list_submodules(
                module,
                cache_dir=ctx.cache_dir,
                github_token=ctx.github_token,
            )

        if not submodules:
            console.print(f"[yellow]No submodules found for '{module}'.[/yellow]")
            return

        # Create and display table
        table = Table(title=f"Submodules in '{module}'", show_header=True, header_style="bold magenta")
        table.add_column("Submodule", style="cyan")
        table.add_column("Full Path", style="green")

        for submodule in submodules:
            full_path = f"{module}/{submodule}"
            table.add_row(submodule, full_path)

        console.print(table)
        console.print(f"\n[green]Total: {len(submodules)} submodules[/green]")

    except Exception as e:
        console.print(f"[red]Error listing submodules: {e}[/red]", style="bold")
        raise click.Abort()


@cli.command()
@click.argument("module")
@click.option(
    "--force",
    is_flag=True,
    help="Force re-download even if module is cached.",
)
@pass_context
def download(ctx: CLIContext, module: str, force: bool):
    """Download an nf-core module.

    Example: pynf download fastqc
    """
    try:
        with console.status(f"[bold green]Downloading '{module}'..."):
            nf_module = tools.download_module(
                module,
                cache_dir=ctx.cache_dir,
                force=force,
                github_token=ctx.github_token,
            )

        console.print(f"\n[green]✓ Module downloaded successfully![/green]")
        console.print(f"  Location: [cyan]{nf_module.local_path}[/cyan]")
        console.print(f"  main.nf: [cyan]{nf_module.main_nf}[/cyan]")
        console.print(f"  meta.yml: [cyan]{nf_module.meta_yml}[/cyan]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]", style="bold")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]", style="bold")
        raise click.Abort()


@cli.command("list-inputs")
@click.argument("module")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON.",
)
@pass_context
def list_inputs(ctx: CLIContext, module: str, output_json: bool):
    """List input parameters from a module's meta.yml.

    Example: pynf list-inputs fastqc
    """
    with console.status(f"[bold green]Fetching inputs for '{module}'..."):
        inputs = tools.get_module_inputs(
            module,
            cache_dir=ctx.cache_dir,
            github_token=ctx.github_token,
        )

    if output_json:
        console.print_json(data=inputs)
        return

    console.print(f"\n[bold magenta]Module: {module}[/bold magenta]\n")
    for group_idx, input_group in enumerate(inputs):
        table = _format_input_group_table(group_idx, input_group)
        console.print(table)
        if group_idx < len(inputs) - 1:
            console.print()


@cli.command()
@click.argument("module")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON.",
)
@pass_context
def inspect(ctx: CLIContext, module: str, output_json: bool):
    """Inspect a downloaded nf-core module.

    Displays the meta.yml file and module paths.

    Example: pynf inspect fastqc
    """
    try:
        with console.status(f"[bold green]Inspecting '{module}'..."):
            info = tools.inspect_module(
                module,
                cache_dir=ctx.cache_dir,
                github_token=ctx.github_token,
            )

        if output_json:
            # Output as JSON
            console.print_json(data=info["meta"])
        else:
            # Display as formatted text
            console.print(f"\n[bold magenta]Module: {info['name']}[/bold magenta]")
            console.print(f"[cyan]Location:[/cyan] {info['path']}")
            console.print(f"\n[bold cyan]meta.yml:[/bold cyan]")
            console.print(info["meta_raw"])

            console.print(f"\n[bold cyan]main.nf:[/bold cyan] ({info['main_nf_lines']} lines)")
            # Show preview
            for line in info["main_nf_preview"]:
                console.print(line)
            if info["main_nf_lines"] > 20:
                console.print(f"[dim]... ({info['main_nf_lines'] - 20} more lines)[/dim]")

    except Exception as e:
        console.print(f"[red]Error inspecting module: {e}[/red]", style="bold")
        raise click.Abort()


@cli.command()
@click.argument("module")
@click.option(
    "--inputs",
    type=str,
    default=None,
    help="Inputs as JSON string. Format: '[{\"param1\": \"value1\"}, {\"param2\": \"value2\"}]'",
)
@click.option(
    "--params",
    type=str,
    default=None,
    help="Parameters as JSON string or key=value pairs.",
)
@click.option(
    "--docker",
    is_flag=True,
    help="Enable Docker execution.",
)
@click.option(
    "--executor",
    type=str,
    default="local",
    help="Nextflow executor (local, slurm, etc.). Defaults to 'local'.",
)
@pass_context
def run(
    ctx: CLIContext,
    module: str,
    inputs: Optional[str],
    params: Optional[str],
    docker: bool,
    executor: str,
):
    """Run an nf-core module.

    Automatically downloads the module if not present locally.

    Example:
        pynf run fastqc --inputs '[{"meta": {"id": "sample1"}, "reads": ["sample.fastq"]}]'
    """
    try:
        # Parse parameters
        parsed_params = {}
        if params:
            try:
                # Try JSON first
                if params.startswith("{"):
                    parsed_params = json.loads(params)
                else:
                    # Parse key=value pairs
                    for pair in params.split(","):
                        key, value = pair.strip().split("=")
                        # Try to parse value as JSON, else keep as string
                        try:
                            parsed_params[key] = json.loads(value)
                        except json.JSONDecodeError:
                            parsed_params[key] = value
            except Exception as e:
                console.print(f"[red]Error parsing parameters: {e}[/red]")
                raise click.Abort()

        # Parse inputs
        parsed_inputs = None
        if inputs:
            try:
                parsed_inputs = json.loads(inputs)
                if not isinstance(parsed_inputs, list):
                    console.print(f"[red]Error: inputs must be a JSON list of dicts[/red]")
                    raise click.Abort()
            except json.JSONDecodeError as e:
                console.print(f"[red]Error parsing inputs (must be valid JSON list): {e}[/red]")
                raise click.Abort()

        # Display execution info
        console.print(f"\n[bold green]Running module: {module}[/bold green]")
        console.print(f"[cyan]Executor: {executor}[/cyan]")
        if parsed_inputs:
            console.print(f"[cyan]Inputs: {parsed_inputs}[/cyan]")
        if parsed_params:
            console.print(f"[cyan]Params: {parsed_params}[/cyan]")
        console.print()

        # Run the module
        with console.status("[bold green]Executing..."):
            result = tools.run_nfcore_module(
                module,
                inputs=parsed_inputs,
                params=parsed_params,
                executor=executor,
                docker_enabled=docker,
                cache_dir=ctx.cache_dir,
                github_token=ctx.github_token,
            )

        # Display results
        console.print("\n[bold green]✓ Module execution completed![/bold green]")

        output_files = result.get_output_files()
        if output_files:
            console.print(f"\n[bold cyan]Output files:[/bold cyan]")
            for file in output_files:
                console.print(f"  • {file}")

        workflow_outputs = result.get_workflow_outputs()
        if workflow_outputs:
            console.print(f"\n[bold cyan]Workflow outputs:[/bold cyan]")
            for output in workflow_outputs:
                console.print(f"  • {output['name']}: {output['value']}")

    except Exception as e:
        console.print(f"[red]Error running module: {e}[/red]", style="bold")
        raise click.Abort()


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
