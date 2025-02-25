import json
import logging
import random
import time
import uuid
import warnings
from typing import List, Dict, Any, Optional
import concurrent.futures

import click
from langsmith.utils import LangSmithMissingAPIKeyWarning
from pyfiglet import Figlet
from rich.console import Console
from rich.live import Live
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn, MofNCompleteColumn, TaskID
from rich.table import Table

from . import __version__
from .storage import (
    get_all_results,
    get_all_api_keys,
    insert_api_key,
    get_results_by_agent,
    get_results_by_run_id
)
from .datasets import load_task_data, get_all_task_ids
from .executor import TaskExecutor

logging.basicConfig(
    level="ERROR",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
warnings.filterwarnings("ignore", category=LangSmithMissingAPIKeyWarning)


def print_ascii(console: Optional[Console] = None):
    if console is None:
        console = Console()
    f = Figlet(font='slant')
    ascii_art = f.renderText('actbench')
    console.print(f"[bold white]{ascii_art}[/bold white]")


def generate_summary_table(results_: List[Dict[str, Any]], run_id: str) -> Table:
    table = Table(title="Benchmark Summary", show_header=True, header_style="bold magenta")
    table.add_column("Run ID", style="dim")
    table.add_column("Agent", style="dim")
    table.add_column("Tasks Run", justify="right")
    table.add_column("Success Rate", justify="right")
    table.add_column("Avg. Latency (ms)", justify="right")
    table.add_column("Avg. Score", justify="right")
    table.add_column("Error Rate", justify="right")

    agent_stats: Dict[str, Dict[str, Any]] = {}
    for result in results_:
        agent = result['agent']
        if agent not in agent_stats:
            agent_stats[agent] = {
                'total': 0,
                'success': 0,
                'total_latency': 0,
                'total_score': 0,
                'errors': 0
            }
        agent_stats[agent]['total'] += 1
        if result['success']:
            agent_stats[agent]['success'] += 1
            agent_stats[agent]['total_latency'] += result.get("latency_ms", -1)
            agent_stats[agent]['total_score'] += result.get("score", 0)
        else:
            agent_stats[agent]['errors'] += 1

    for agent, stats in agent_stats.items():
        total_tasks = stats['total']
        success_rate = (stats['success'] / total_tasks) * 100 if total_tasks > 0 else 0.0
        avg_latency = stats['total_latency'] / stats['success'] if stats['success'] > 0 else 0.0
        avg_score = stats['total_score'] / stats['success'] if stats['success'] > 0 else 0.0
        error_rate = (stats['errors'] / total_tasks) * 100 if total_tasks > 0 else 0.0

        table.add_row(
            run_id,
            agent,
            str(total_tasks),
            f"{success_rate:.2f}%",
            f"{avg_latency:.2f}",
            f"{avg_score:.2f}",
            f"{error_rate:.2f}%",
        )
    return table


def submit_task(task_id: str, agent_name: str, api_keys, console: Console, run_id: str, no_scoring: bool,
                progress: Progress, task_progress: TaskID):
    try:
        if isinstance(task_id, str) and task_id.isdigit():
            task_id = int(task_id)
        task_data = load_task_data(task_id)
        executor = TaskExecutor(agent_name, api_keys, task_data, run_id, no_scoring)
        result = executor.run()
        progress.update(task_progress, advance=1)
        return result

    except (FileNotFoundError, KeyError) as e:
        console.print(f"Error loading task data for ID {task_id}: {e}", style="bold red")
        progress.update(task_progress, advance=1)
        return {"success": False, "response": str(e), 'task_id': task_id, 'agent': agent_name, "latency_ms": -1,
                "timestamp": int(time.time() * 1000), "score": -1, "run_id": run_id}
    except Exception as e:
        console.print(f"An unexpected error occurred loading/running task data for ID {task_id}: {e}",
                      style="bold red")
        progress.update(task_progress, advance=1)
        return {"success": False, "response": str(e), 'task_id': task_id, 'agent': agent_name, "latency_ms": -1,
                "timestamp": int(time.time() * 1000), "score": -1, "run_id": run_id}


@click.group(invoke_without_command=True)
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
    """
    ActBench: A framework for evaluating web automation frameworks and LAM systems.
    """
    if ctx.invoked_subcommand is None:
        print_ascii()
        click.echo(ctx.get_help())


@cli.command()
def list_tasks():
    """List available tasks in the dataset."""
    task_ids = get_all_task_ids()
    if not task_ids:
        click.echo("No tasks found.")
        return

    click.echo("Available Tasks:")
    for task_id in task_ids:
        click.echo(f"  - {task_id}")


@cli.command()
@click.option('--task', '-t', help='Task ID to run (e.g., 256). Can be specified multiple times.', multiple=True)
@click.option('--agent', '-a', help='Agent to use (e.g., raccoonai). Can be specified multiple times.', multiple=True)
@click.option('--random-tasks', '-r', type=int, default=0,
              help='Run a specified number of random tasks.')
@click.option('--all-tasks', '-at', is_flag=True, help='Run all available tasks.')
@click.option('--all-agents', '-aa', is_flag=True, help='Run on all available agents (requires stored API keys).')
@click.option('--parallel', '-p', type=click.IntRange(1, 20), default=1,
              help='Number of tasks to run in parallel (default: 1, max: 20).')
@click.option('--rate-limit', '-rl', type=float, default=0.1,
              help='Delay between tasks when running in parallel (in seconds).')
@click.option('--no-scoring', '-ns', is_flag=True, help='Disable LLM-based scoring.')
def run(task: List[str], agent: List[str], random_tasks: int, all_tasks: bool, all_agents: bool, parallel: int,
        rate_limit: float, no_scoring: Optional[bool] = False):
    """Run benchmark tasks."""

    if not task and random_tasks == 0 and not all_tasks:
        raise click.ClickException("Must specify at least one of --task, --random-tasks, or --all-tasks.")
    if not agent and not all_agents:
        raise click.ClickException("Must specify at least one of --agent or --all-agents.")

    task_ids_to_run = []
    if all_tasks:
        task_ids_to_run = get_all_task_ids()
    elif task:
        task_ids_to_run = list(task)

    if random_tasks > 0:
        all_task_ids = get_all_task_ids()
        if random_tasks > len(all_task_ids):
            click.echo(
                f"Warning: Requested {random_tasks} random tasks, but only {len(all_task_ids)} are available.  Running all.")
            task_ids_to_run = all_task_ids
        else:
            task_ids_to_run = random.sample(all_task_ids, random_tasks)

    api_keys = get_all_api_keys()

    if not no_scoring and 'openai' not in api_keys:
        raise click.ClickException(
            "OpenAI API key is required for scoring. Use `actbench set-key --agent openai`."
            "\nAlternatively, run with the --no-scoring flag to disable scoring.")

    if all_agents:
        agent = list(api_keys.keys())
        if not agent:
            raise click.ClickException("No API keys are stored. Use `set-key` to store keys.")
    for a in agent:
        if a not in api_keys and a != "openai":
            raise click.ClickException(f"API key not set for agent: {a}. Use `actbench set-key --agent {a}`.")

    total_tasks = len(task_ids_to_run) * len(agent)

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    )

    console = Console()
    print_ascii(console)
    all_results = []
    run_id = uuid.uuid4().hex[:8]

    with Live(progress, console=console, refresh_per_second=12) as live:
        task_progress = progress.add_task("Running...", total=total_tasks)
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = []
            for task_id in task_ids_to_run:
                for agent_name in agent:
                    if agent_name == "openai":
                        continue
                    future = executor.submit(submit_task, task_id, agent_name, api_keys, console, run_id, no_scoring,
                                             progress, task_progress)
                    futures.append(future)
                    time.sleep(rate_limit)

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                all_results.append(result)

        end_time = time.time()
        elapsed_time = end_time - start_time
        live.stop()
        console.print(f"Total elapsed time: {elapsed_time:.2f} seconds")

        summary_table = generate_summary_table(all_results, run_id)
        console.print(summary_table)
        console.print("\n[bold green]Benchmark run completed![/bold green]")


@cli.command()
@click.option('--agent', '-a', required=True, help='Agent name (e.g., raccoonai).')
def set_key(agent):
    """Set the API key for an agent."""
    key = click.prompt(f"Enter API key for {agent}", hide_input=True, type=str)
    insert_api_key(agent, key)
    click.echo(f"API key set for {agent}.")


@cli.group()
def results():
    """Manage and view benchmark results."""
    pass


@results.command("list")
@click.option('--agent', '-a', required=False, help='Agent name (e.g., raccoonai).')
@click.option('--run-id', '-r', required=False, help='Run ID.')
def list_results(agent: Optional[str] = None, run_id: Optional[str] = None):
    """List all benchmark results."""
    if agent:
        all_results = get_results_by_agent(agent)
    elif run_id:
        all_results = get_results_by_run_id(run_id)
    else:
        all_results = get_all_results()

    if not all_results:
        if agent:
            click.echo(f"No results found for agent {agent}.")
        else:
            click.echo("No results found.")
        return

    click.echo("Benchmark Results:")
    for row in all_results:
        click.echo("-" * 30)
        click.echo(f"Run ID: {row['run_id']}")
        click.echo(f"Task ID: {row['task_id']}")
        click.echo(f"Agent: {row['agent']}")
        click.echo(f"Timestamp: {row['timestamp']}")
        click.echo(f"Success: {row['success']}")
        click.echo(f"Latency (ms): {row['latency_ms'] if row['latency_ms'] != -1 else 'N/A'}")
        click.echo(f"Score: {row['score']}")
        click.echo(f"Response: {row['response'] if row['response'] else 'N/A'}")
    click.echo("-" * 30)


@results.command("export")
@click.option('--agent', '-a', required=False, help='Agent name (e.g., raccoonai).')
@click.option('--run-id', '-r', required=False, help='Run ID.')
@click.option('--format', '-f', 'format_', type=click.Choice(['json', 'csv']), default='json',
              help='Export format.')
@click.option('--output', '-o', type=click.Path(), help='Output file path.')
def export(format_: str, agent: Optional[str] = None, run_id: Optional[str] = None, output: Optional[str] = None):
    """Export all benchmark results in JSON or CSV format."""
    if agent:
        all_results = get_results_by_agent(agent)
    elif run_id:
        all_results = get_results_by_run_id(run_id)
    else:
        all_results = get_all_results()

    if not all_results:
        if agent:
            click.echo(f"No results found for agent {agent}.")
        elif run_id:
            click.echo(f"No results found for run ID {run_id}.")
        else:
            click.echo("No results found.")
        return

    if output:
        try:
            if format_ == 'json':
                with open(output, 'w') as f:
                    json.dump(all_results, f, indent=2)
            elif format_ == 'csv':
                with open(output, 'w') as f:
                    if all_results:
                        header = list(all_results[0].keys())
                        f.write(','.join(header) + '\n')
                        for row in all_results:
                            f.write(','.join(str(row[key]) for key in header) + '\n')
            click.echo(f"Results exported to {output}")
        except Exception as e:
            click.echo(f"Error writing to file: {e}", err=True)
    else:
        if format_ == 'json':
            click.echo(json.dumps(all_results, indent=2))
        elif format_ == 'csv':
            if all_results:
                header = list(all_results[0].keys())
                click.echo(','.join(header))
                for row in all_results:
                    click.echo(','.join(str(row[key]) for key in header))


@cli.command()
def list_agents():
    """List all agents for which API keys are stored."""
    api_keys = get_all_api_keys()
    if api_keys:
        click.echo("Agents with stored API keys:")
        for agent in api_keys:
            click.echo(f"  - {agent}")
    else:
        click.echo("No API keys are currently stored.")


if __name__ == '__main__':
    cli()
