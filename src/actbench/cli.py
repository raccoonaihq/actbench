import logging
import click
import json
import random
from typing import List

from .database import (
    get_all_results,
    get_all_api_keys,
    insert_api_key,
)
from .datasets import load_task_data, get_available_categories, get_task_ids_by_category
from .runner import TaskExecutor, BenchmarkRunner
from . import __version__

logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@click.group()
@click.version_option(__version__)
def cli():
    """
    ActBench: A benchmarking framework for evaluating and web automation frameworks and LAM systems.

    ActBench provides a command-line interface for running benchmarks, managing API keys,
    and viewing results.
    """
    pass


@cli.command()
@click.option('--category', '-c', help='List tasks within a specific category (e.g., run/ecommerce).')
def list_tasks(category):
    """List available benchmark tasks.

    You can list all tasks or filter by category.
    """
    if category:
        try:
            task_ids = get_task_ids_by_category(category)
            if not task_ids:
                click.echo(f"No tasks found in category '{category}'.")
                return
            click.echo(f"Tasks in category '{category}':")
            for task_id in task_ids:
                click.echo(f"  - {task_id}")

        except FileNotFoundError:
            click.echo(f"Category not found: {category}")
        except Exception:
            click.echo(f"Invalid args")
    else:
        categories = get_available_categories()
        if not categories:
            click.echo("No task categories found.")
            return

        for category in categories:
            click.echo(f"Category - {category}")
            try:
                task_ids = get_task_ids_by_category(category)
                if not task_ids:
                    click.echo(f"No tasks found in category '{category}'.")
                    return
                click.echo(f"Tasks in category '{category}':")
                for task_id in task_ids:
                    click.echo(f"  - {task_id}")
            except FileNotFoundError:
                click.echo(f"Category not found: {category}")
            except Exception:
                click.echo(f"Invalid args")


@cli.command()
@click.option('--task', '-t', help='Task ID to run (e.g., run/ecommerce/task_1). Can be specified multiple times.',
              multiple=True)
@click.option('--category', '-c',
              help='Category to run tasks from (e.g., run/ecommerce). Can be specified multiple times.', multiple=True)
@click.option('--agent', '-a', help='Agent to use (e.g., raccoonai). Can be specified multiple times.', multiple=True)
@click.option('--random-tasks', '-r', type=int, default=0,
              help='Run a specified number of random tasks. If combined with --category, selects random tasks within '
                   'the categories.')
@click.option('--all-tasks', is_flag=True, help='Run all available tasks.')
@click.option('--all-agents', is_flag=True, help='Run on all available agents (requires stored API keys).')
def run(task: List[str], category: List[str], agent: List[str], random_tasks: int, all_tasks: bool, all_agents: bool):
    """Run benchmark tasks against specified agents.

    This command allows you to run specific tasks, tasks from categories,
    a random selection of tasks, or all tasks. You can also specify
    which agents to use, or run against all agents with stored API keys.
    """

    if not task and not category and random_tasks == 0 and not all_tasks:
        raise click.ClickException("Must specify at least one of --task, --category, --random-tasks, or --all-tasks.")
    if not agent and not all_agents:
        raise click.ClickException("Must specify at least one of --agent or --all-agents.")

    task_ids_to_run = []
    if all_tasks:
        for cat in get_available_categories():
            task_ids_to_run.extend(get_task_ids_by_category(cat))
    elif category:
        for cat in category:
            task_ids_to_run.extend(get_task_ids_by_category(cat))
    if task:
        task_ids_to_run.extend(task)

    if random_tasks > 0:
        if not task_ids_to_run:
            for cat in get_available_categories():
                task_ids_to_run.extend(get_task_ids_by_category(cat))

        if random_tasks > len(task_ids_to_run):
            click.echo(
                f"Warning: Requested {random_tasks} random tasks, but only {len(task_ids_to_run)} are available. Running all selected tasks.")
        else:
            task_ids_to_run = random.sample(task_ids_to_run, random_tasks)

    api_keys = get_all_api_keys()

    if all_agents:
        agent = list(api_keys.keys())
        if not agent:
            raise click.ClickException("No API keys are stored. Use `set-key` to store keys.")
    for a in agent:
        if a not in api_keys:
            raise click.ClickException(f"API key not set for agent: {a}. Use `actbench set-key --agent {a}`.")

    for task_id in task_ids_to_run:
        parts = task_id.split("/")
        if len(parts) != 3:
            click.echo(f"Invalid task_id format {task_id}, skipping", err=True)
            continue
        task_type, category_name, actual_task_id = parts

        try:
            task_data = load_task_data(task_type, category_name, actual_task_id)
        except FileNotFoundError:
            click.echo(f"Task Data not found for ID {task_id}, skipping", err=True)
            continue

        for agent_name in agent:
            click.echo(f"Running task '{task_id}' with agent '{agent_name}'...")
            executor = TaskExecutor(agent_name, api_keys, task_data, task_type)
            result = executor.run()
            click.echo(json.dumps(result, indent=2))


@cli.command()
def benchmark():
    """Run all tasks on all agents (requires stored keys).

    This is a convenience command equivalent to `actbench run --all-tasks --all-agents`.
    """
    api_keys = get_all_api_keys()
    if not api_keys:
        click.echo("No API keys are stored. Use `set-key` to store keys.")
        return

    runner = BenchmarkRunner(api_keys)
    benchmark_results = runner.run()
    click.echo(f"Benchmark complete. Results stored in database.")


@cli.command()
@click.option('--agent', '-a', required=True, help='Agent name (e.g., raccoonai).')
def set_key(agent):
    """Set the API key for an agent.

    The API key will be stored *persistently* in the ActBench database.
    """
    click.echo("API keys are stored in plain text in the database.")
    key = click.prompt(f"Enter API key for {agent}", hide_input=True, type=str)
    insert_api_key(agent, key)
    click.echo(f"API key set for {agent}.")


@cli.group()
def results():
    """Manage and view benchmark results."""
    pass


@results.command("list")
def list_results():
    """List all benchmark results.
    """
    all_results = get_all_results()

    if not all_results:
        click.echo("No results found in the database.")
        return

    click.echo("Benchmark Results:")
    for row in all_results:
        click.echo("-" * 30)
        click.echo(f"Task ID: {row['task_id']}")
        click.echo(f"Agent: {row['agent']}")
        click.echo(f"Timestamp: {row['timestamp']}")
        click.echo(f"Success: {row['success']}")
        click.echo(f"Latency (ms): {row['latency_ms'] if row['latency_ms'] != -1 else 'N/A'}")
        click.echo(f"Error: {row['error'] if row['error'] else 'N/A'}")
    click.echo("-" * 30)


@results.command("export")
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json', help='Export format.')
def export(format: str):
    """Export all benchmark results in JSON or CSV format."""
    all_results = get_all_results()  # Consistent variable name
    if not all_results:
        click.echo("No Results to export")
        return

    if format == 'json':
        click.echo(json.dumps(all_results, indent=2))
    elif format == 'csv':
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
