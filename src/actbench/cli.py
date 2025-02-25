import concurrent.futures
import json
import logging
import os
import random
import signal
import threading
import time
import uuid
import warnings
from typing import List, Dict, Any, Optional

import click
from langsmith.utils import LangSmithMissingAPIKeyWarning
from pyfiglet import Figlet
from rich.console import Console
from rich.live import Live
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn, MofNCompleteColumn
from rich.table import Table

from . import __version__
from .datasets import load_task_data, get_all_task_ids, get_all_tasks
from .executor import TaskExecutor
from .storage import (
    get_all_results,
    get_all_api_keys,
    insert_api_key,
    get_results_by_agent,
    get_results_by_run_id
)

logging.basicConfig(
    level="ERROR",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
warnings.filterwarnings("ignore", category=LangSmithMissingAPIKeyWarning)
shutdown_in_progress = False
live: Live | None = None
progress: Progress | None = None


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


def submit_task(task_id, agent_name, api_keys, console, run_id, no_scoring,
                progress_, task_progress, terminate_event):
    try:
        if terminate_event.is_set():
            return {"success": False, "response": "User interrupted.", 'task_id': task_id, 'agent': agent_name,
                    "latency_ms": -1, "timestamp": int(time.time() * 1000), "score": -1, "run_id": run_id}

        if isinstance(task_id, str) and task_id.isdigit():
            task_id = int(task_id)
        task_data = load_task_data(task_id)
        executor = TaskExecutor(agent_name, api_keys, task_data, run_id, no_scoring)
        result = executor.run()

        if not terminate_event.is_set():
            progress_.update(task_progress, advance=1)
        return result

    except Exception as e:
        if not terminate_event.is_set():
            console.print(f"Error in task {task_id}: {str(e)}", style="bold red")
            progress_.update(task_progress, advance=1)
        return {"success": False, "response": str(e), 'task_id': task_id, 'agent': agent_name,
                "latency_ms": -1, "timestamp": int(time.time() * 1000), "score": -1, "run_id": run_id}


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="actbench")
@click.pass_context
def cli(ctx):
    """
    actbench, a framework for evaluating web automation agents and LAM systems.
    """
    if ctx.invoked_subcommand is None:
        print_ascii()
        click.echo(ctx.get_help())


@cli.group(name="tasks", help="Manage benchmark tasks.")
def tasks():
    pass


@tasks.command(name="list", help="List available tasks.")
def list_tasks():
    """List available tasks in the dataset."""
    tasks_ = get_all_tasks()
    if not tasks:
        click.echo("No tasks found.")
        return

    console = Console()
    table = Table(title="Available Tasks", show_header=True, header_style="bold magenta")
    table.add_column("Task ID", style="dim", justify="right")
    table.add_column("Query", style="cyan")
    table.add_column("Url", style="dim")
    table.add_column("Complexity")
    table.add_column("Requires Login", style="green")
    for task in tasks_:
        table.add_row(
            str(task["task_id"]),
            task["query"],
            task["url"],
            "[green]Low[/green]" if task["complexity"] == 'low' else "[yellow]Medium[/yellow]"
            if task["complexity"] == 'medium' else "[red]High[/red]",
            "[green]Yes[/green]" if task["requires_login"] else "[red]No[/red]",
        )

    console.print(table)


@cli.command(name="run", help="Run benchmark tasks.")
@click.option("--task", "-t", multiple=True, help="Specific task ID(s) to run.")
@click.option("--agent", "-a", multiple=True, help="Agent(s) to use.")
@click.option("--random", "-r", "random_tasks", type=int, default=0, help="Run a number of random tasks.")
@click.option("--all-tasks", is_flag=True, help="Run all available tasks.")
@click.option("--all-agents", is_flag=True, help="Run with all configured agents.")
@click.option("--parallel", "-p", type=click.IntRange(1, 20), default=1, help="Number of tasks to run in parallel.")
@click.option("--rate-limit", "-l", type=float, default=0.1, help="Delay between tasks (seconds).")
@click.option("--no-scoring", "-ns", is_flag=True, help="Disable LLM-based scoring.")
def run(task: List[str], agent: List[str], random_tasks: int, all_tasks: bool, all_agents: bool, parallel: int,
        rate_limit: float, no_scoring: Optional[bool] = False):
    """Run benchmark tasks."""

    if not any([task, random_tasks, all_tasks]):
        raise click.ClickException("Must specify tasks to run: --task, --random, or --all-tasks.")
    if not any([agent, all_agents]):
        raise click.ClickException("Must specify agents: --agent or --all-agents.")

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
    global progress
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

    terminate_event = threading.Event()

    def handle_interrupt(signum, frame):
        """Handle interrupt signal (CTRL+C)"""
        global shutdown_in_progress, live, progress
        progress = None
        if live:
            live.stop()

        if shutdown_in_progress:
            console.print("\n[bold red]Forced exit. Some tasks may not be properly cleaned up.[/bold red]")
            os._exit(1)

        shutdown_in_progress = True
        console.print("\n[bold yellow]Interrupt received. Stopping tasks (this may take a moment)...[/bold yellow]")

        terminate_event.set()

    original_sigint_handler = signal.signal(signal.SIGINT, handle_interrupt)
    original_sigterm_handler = signal.signal(signal.SIGTERM, handle_interrupt)
    try:
        with Live(progress, console=console, refresh_per_second=12) as live_:
            global live
            live = live_
            task_progress = progress.add_task("Running...", total=total_tasks)
            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:

                futures = []
                for task_id in task_ids_to_run:
                    if terminate_event.is_set():
                        break
                    for agent_name in agent:
                        if agent_name == "openai":
                            continue
                        future = executor.submit(submit_task, task_id, agent_name, api_keys, console, run_id,
                                                 no_scoring,
                                                 progress, task_progress, terminate_event)
                        futures.append(future)
                        time.sleep(rate_limit)

                try:
                    completed_futures = []
                    for future in concurrent.futures.as_completed(futures):
                        if terminate_event.is_set():
                            break
                        result = future.result()
                        all_results.append(result)
                        completed_futures.append(future)
                except KeyboardInterrupt:
                    terminate_event.set()
                    console.print("\n[bold yellow]Interrupt caught. Cleaning up...[/bold yellow]")

                if terminate_event.is_set():
                    for future in futures:
                        if future not in completed_futures and not future.done():
                            future.cancel()
    finally:
        signal.signal(signal.SIGINT, original_sigint_handler)
        signal.signal(signal.SIGTERM, original_sigterm_handler)

        if not terminate_event.is_set() and all_results:
            end_time = time.time()
            elapsed_time = end_time - start_time
            console.print(f"Total elapsed time: {elapsed_time:.2f} seconds")

            summary_table = generate_summary_table(all_results, run_id)
            console.print(summary_table)
            console.print("\n[bold green]Benchmark run completed![/bold green]")
        elif terminate_event.is_set():
            console.print("\n[bold yellow]Benchmark run was interrupted.[/bold yellow]")
        else:
            console.print("\n[bold yellow]No results collected.[/bold yellow]")


@cli.command(name="set-key", help="Set an API key for an agent.")
@click.option('--agent', '-a', required=True, help='Agent name (e.g., raccoonai).')
def set_key(agent):
    """Set the API key for an agent."""
    key = click.prompt(f"Enter API key for {agent}", hide_input=True, type=str)
    insert_api_key(agent, key)
    click.echo(f"API key set for {agent}.")


@cli.group(name="results", help="Manage and view benchmark results.")
def results():
    pass


@results.command(name="list", help="List benchmark results.")
@click.option("--agent", "-a", required=False, help="Filter results by agent.")
@click.option("--run-id", "-r", required=False, help="Filter results by run ID.")
def list_results(agent: Optional[str] = None, run_id: Optional[str] = None):
    if agent:
        all_results = get_results_by_agent(agent)
    elif run_id:
        all_results = get_results_by_run_id(run_id)
    else:
        all_results = get_all_results()

    console = Console()

    if not results:
        console.print("No results found.", style="yellow")
        return

    table = Table(title="Benchmark Results", show_header=True, header_style="bold magenta")
    table.add_column("Run ID", style="dim")
    table.add_column("Task ID", style="dim", justify="right")
    table.add_column("Agent", style="cyan")
    table.add_column("Timestamp", justify="right")
    table.add_column("Success", justify="center")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Response", style="green")

    for row in all_results:
        table.add_row(
            row['run_id'],
            str(row['task_id']),
            row['agent'],
            str(row['timestamp']),
            "[green]Yes[/green]" if row['success'] else "[red]No[/red]",
            str(row['latency_ms']),
            str(row['score']),
            row['response'] if row['response'] else 'N/A'
        )

    console.print(table)


@results.command(name="export", help="Export results to a file.")
@click.option("--agent", "-a", help="Filter results by agent.")
@click.option("--run-id", "-r", help="Filter results by run ID.")
@click.option("--format", "-f", "format_", type=click.Choice(['json', 'csv']), default='json', help="Export format.")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output file path.")
def export_results(agent: Optional[str], run_id: Optional[str], format_: str, output: str):
    console = Console()
    if agent:
        results_ = get_results_by_agent(agent)
    elif run_id:
        results_ = get_results_by_run_id(run_id)
    else:
        results_ = get_all_results()

    if not results_:
        console.print("No results to export.", style="yellow")
        return

    try:
        if format_ == 'json':
            with open(output, 'w') as f:
                json.dump(results_, f, indent=2)
        elif format_ == 'csv':
            with open(output, 'w') as f:
                if results_:
                    header = list(results_[0].keys())
                    f.write(','.join(header) + '\n')
                    for row in results_:
                        f.write(','.join(str(row[key]) for key in header) + '\n')
        console.print(f"Results exported to [bold]{output}[/bold] in {format_} format.", style="green")
    except Exception as e:
        console.print(f"Error exporting results: {e}", style="red")


@cli.group(name="agents", help="View agents and API keys..")
def agents():
    pass


@agents.command(name="list", help="List configured agents.")
def list_agents():
    """List all agents for which API keys are stored."""
    console = Console()

    supported_agents = ['Agent', 'raccoonai']
    table = Table(title="Supported Agents", show_header=False, header_style="bold magenta")
    table.add_row(*supported_agents)
    table.columns[0].style = 'cyan'
    console.print(table)

    api_keys = get_all_api_keys()
    if api_keys:
        table = Table(title="Agents with Stored API Keys", show_header=True, header_style="bold magenta")
        table.add_column("Agent", style="cyan")
        table.add_column("API Key", style="white")
        for agent in api_keys:
            table.add_row(agent, api_keys[agent])
        console.print(table)
    else:
        console.print("No API keys are currently stored.")


if __name__ == '__main__':
    cli()
