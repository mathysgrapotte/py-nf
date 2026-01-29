"""Click CLI for managing nf-core modules and Nextflow scripts."""

import click
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from datetime import datetime

from . import api
from .cli_app import CLIContext
from .cli_parsing import parse_inputs_option, parse_params_option
from .cli_rendering import input_group_table, modules_table
from .module_service import ensure_module
from .types import DockerConfig, ExecutionRequest

# Create a rich console for pretty printing
console = Console()


def _format_input_group_table(group_idx: int, input_group) -> Table:
    """Format an input channel into a rich table.

    Args:
        group_idx: Zero-based index of the input channel.
        input_group: Input channel mapping from native API introspection.

    Returns:
        Rich table describing the input channel.
    """
    return input_group_table(group_idx, input_group)


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
    """Entry point for the pynf CLI commands.

    Args:
        ctx: Click context populated by the command group.
        cache_dir: Optional cache directory override.
        github_token: Optional GitHub token for authenticated requests.
    """
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
    """List available nf-core modules.

    Args:
        ctx: Click context containing CLI configuration.
        limit: Optional number of modules to display.
        rate_limit: When ``True``, display GitHub API rate limit info.
    """
    try:
        with console.status("[bold green]Fetching modules..."):
            cache_dir = ctx.cache_dir or api.DEFAULT_CACHE_DIR
            modules = api.list_modules(
                cache_dir=cache_dir, github_token=ctx.github_token
            )

        if not modules:
            console.print("[yellow]No modules found.[/yellow]")
            return

        display_modules = modules[:limit] if limit else modules
        table = modules_table(modules, limit=limit)
        console.print(table)

        # Show count
        total = len(modules)
        shown = len(display_modules)
        if limit and shown < total:
            console.print(
                f"\n[yellow]Showing {shown}/{total} modules (use --limit to see more)[/yellow]"
            )
        else:
            console.print(f"\n[green]Total: {total} modules[/green]")

        # Show rate limit if requested
        if rate_limit:
            try:
                status = api.get_rate_limit_status(github_token=ctx.github_token)
                rate_table = Table(
                    title="GitHub API Rate Limit",
                    show_header=True,
                    header_style="bold blue",
                )
                rate_table.add_column("Metric", style="cyan")
                rate_table.add_column("Value", style="green")
                rate_table.add_row("Limit", str(status["limit"]))
                rate_table.add_row("Remaining", str(status["remaining"]))
                reset_time = datetime.fromtimestamp(status["reset_time"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
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

    Args:
        ctx: Click context containing CLI configuration.
        module: Parent module identifier.
    """
    try:
        with console.status(f"[bold green]Fetching submodules for '{module}'..."):
            submodules = api.list_submodules(module, github_token=ctx.github_token)

        if not submodules:
            console.print(f"[yellow]No submodules found for '{module}'.[/yellow]")
            return

        # Create and display table
        table = Table(
            title=f"Submodules in '{module}'",
            show_header=True,
            header_style="bold magenta",
        )
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
    """Download an nf-core module into the local cache.

    Args:
        ctx: Click context containing CLI configuration.
        module: Module identifier to download.
        force: When ``True``, re-download even if cached.
    """
    try:
        with console.status(f"[bold green]Downloading '{module}'..."):
            cache_dir = ctx.cache_dir or api.DEFAULT_CACHE_DIR
            paths = ensure_module(cache_dir, module, ctx.github_token, force=force)

        console.print(f"\n[green]✓ Module downloaded successfully![/green]")
        console.print(f"  Location: [cyan]{paths.module_dir}[/cyan]")
        console.print(f"  main.nf: [cyan]{paths.main_nf}[/cyan]")
        console.print(f"  meta.yml: [cyan]{paths.meta_yml}[/cyan]")

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
    """List input parameters from a module's ``main.nf``.

    Args:
        ctx: Click context containing CLI configuration.
        module: Module identifier.
        output_json: When ``True``, emit JSON output.
    """
    with console.status(f"[bold green]Fetching inputs for '{module}'..."):
        cache_dir = ctx.cache_dir or api.DEFAULT_CACHE_DIR
        inputs = api.get_module_inputs(
            module, cache_dir=cache_dir, github_token=ctx.github_token
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

    Args:
        ctx: Click context containing CLI configuration.
        module: Module identifier.
        output_json: When ``True``, emit JSON output.
    """
    try:
        with console.status(f"[bold green]Inspecting '{module}'..."):
            cache_dir = ctx.cache_dir or api.DEFAULT_CACHE_DIR
            info = api.inspect_module(
                module, cache_dir=cache_dir, github_token=ctx.github_token
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

            console.print(
                f"\n[bold cyan]main.nf:[/bold cyan] ({info['main_nf_lines']} lines)"
            )
            # Show preview
            for line in info["main_nf_preview"]:
                console.print(line)
            if info["main_nf_lines"] > 20:
                console.print(
                    f"[dim]... ({info['main_nf_lines'] - 20} more lines)[/dim]"
                )

    except Exception as e:
        console.print(f"[red]Error inspecting module: {e}[/red]", style="bold")
        raise click.Abort()


@cli.command()
@click.argument("module")
@click.option(
    "--inputs",
    type=str,
    default=None,
    help='Inputs as JSON string. Format: \'[{"param1": "value1"}, {"param2": "value2"}]\'',
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
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose debug output.",
)
@pass_context
def run(
    ctx: CLIContext,
    module: str,
    inputs: Optional[str],
    params: Optional[str],
    docker: bool,
    executor: str,
    verbose: bool,
):
    """Run an nf-core module via the Nextflow runtime.

    Args:
        ctx: Click context containing CLI configuration.
        module: Module identifier.
        inputs: JSON string describing input groups.
        params: JSON string or key=value list of parameters.
        docker: Whether to enable Docker execution.
        executor: Nextflow executor name.
        verbose: Enable verbose debug output.
    """
    try:
        try:
            parsed_params = parse_params_option(params)
            parsed_inputs = parse_inputs_option(inputs)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Error parsing JSON input: {exc}") from exc

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
            cache_dir = ctx.cache_dir or api.DEFAULT_CACHE_DIR
            docker_config = None
            if docker:
                docker_config = DockerConfig(enabled=True, registry="quay.io")
            request = ExecutionRequest(
                script_path=Path(module),
                executor=executor,
                params=parsed_params,
                inputs=parsed_inputs,
                docker=docker_config,
                verbose=verbose,
            )
            result = api.run_module(
                module,
                request,
                cache_dir=cache_dir,
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

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error running module: {e}[/red]", style="bold")
        raise click.Abort()


def main():
    """Main entry point for the CLI.

    Returns:
        ``None``. The CLI handles execution and exits the process.
    """
    cli()


if __name__ == "__main__":
    main()
