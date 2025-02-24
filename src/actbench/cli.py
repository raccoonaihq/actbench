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
from .datasets import load_task_data, get_all_task_ids
from .executor import TaskExecutor
from . import __version__

logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@click.group()
@click.version_option(__version__)
def cli():
    """
    ActBench: A benchmarking framework for evaluating web automation frameworks and LAM systems.
    """
    pass


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
@click.option('--all-tasks', is_flag=True, help='Run all available tasks.')
@click.option('--all-agents', is_flag=True, help='Run on all available agents (requires stored API keys).')
def run(task: List[str], agent: List[str], random_tasks: int, all_tasks: bool, all_agents: bool):
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

    if all_agents:
        agent = list(api_keys.keys())
        if not agent:
            raise click.ClickException("No API keys are stored. Use `set-key` to store keys.")
    for a in agent:
        if a not in api_keys:
            raise click.ClickException(f"API key not set for agent: {a}. Use `actbench set-key --agent {a}`.")

    for task_id in task_ids_to_run:
        try:
            if task_id.isdigit():
                task_id = int(task_id)
            task_data = load_task_data(task_id)
        except (FileNotFoundError, KeyError) as e:
            click.echo(f"Error loading task data for ID {task_id}: {e}", err=True)
            continue
        except Exception as e:
            click.echo(f"An unexpected error occurred loading task data for ID {task_id}: {e}", err=True)
            continue

        for agent_name in agent:
            click.echo(f"Running task '{task_id}' with agent '{agent_name}'...")
            executor = TaskExecutor(agent_name, api_keys, task_data)
            result = executor.run()
            click.echo(json.dumps(result, indent=2))


@cli.command()
@click.option('--agent', '-a', required=True, help='Agent name (e.g., raccoonai).')
def set_key(agent):
    """Set the API key for an agent."""
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
    """List all benchmark results."""
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
        click.echo(f"Response: {row['response'] if row['response'] else 'N/A'}")
    click.echo("-" * 30)


@results.command("export")
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json', help='Export format.')
def export(format: str):
    """Export all benchmark results in JSON or CSV format."""
    all_results = get_all_results()
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
