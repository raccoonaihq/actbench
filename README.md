```
              __  __                    __  
  ____ ______/ /_/ /_  ___  ____  _____/ /_ 
 / __ `/ ___/ __/ __ \/ _ \/ __ \/ ___/ __ \
/ /_/ / /__/ /_/ /_/ /  __/ / / / /__/ / / /
\__,_/\___/\__/_.___/\___/_/ /_/\___/_/ /_/ 
                                  
```         
[![PyPI version](https://img.shields.io/pypi/v/actbench.svg?logo=pypi&&logoColor=white&&color=5d5fef&&cacheSeconds=10)](https://pypi.org/project/actbench/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Requires: Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/release/python-3120/)

## Overview

**actbench** is a extensible framework designed to evaluate the performance and capabilities of web automation agents and LAM systems.


## Installing actbench CLI

**actbench** requires Python 3.12 or higher. We recommend using `pipx` for a clean, isolated installation:

```bash
pipx install actbench
```

## Usage

### 1. Setting API Keys

Before running benchmarks, you need to set API keys for the agents you want to use.

```bash
actbench set-key --agent raccoonai
```

You can list the supported agents and check which API keys are stored:

```bash
actbench agents list
```
### 2. Listing Available Tasks

**actbench** provides a built-in collection of web automation tasks, crafted by merging and refining tasks from the [webarena](https://github.com/web-arena-x/webarena/blob/main/config_files/test.raw.json) and [webvoyager](https://github.com/MinorJerry/WebVoyager/blob/main/data/WebVoyager_data.jsonl) datasets.<br/>
Duplicate tasks have been stripped out, and the queries have been refreshed to align with the most recent information.<br/>
If you want to explore how the tasks have been modified, you can trace their IDs back to the original datasets for a side-by-side comparison.<br/>


To see all the tasks currently available, just run this command:

```bash
actbench tasks list
```

### 3. Running Benchmarks

The `run` command is the heart of **actbench**.  It allows you to execute tasks against specified agents.

#### Basic Usage

```bash
actbench run --agent raccoonai --task 256 --task 424
```

This command runs tasks with IDs `256` and `424` using the `raccoonai` agent.

#### Running All Tasks

```bash
actbench run --agent raccoonai --all-tasks
```

This runs all available tasks using the `raccoonai` agent.

#### Running Random Tasks

```bash
actbench run --agent raccoonai --random 5
```

This runs a random sample of 5 tasks using the `raccoonai` agent.

#### Running with All Agents

```bash
actbench run --all-agents --all-tasks
```

This runs all tasks with all configured agents (for which API keys are stored).

#### Controlling Parallelism

```bash
actbench run --agent raccoonai --all-tasks --parallel 4
```

This runs all tasks using the `raccoonai` agent, executing up to 4 tasks concurrently.

#### Setting Rate Limiting

```bash
actbench run --agent raccoonai --all-tasks --rate-limit 0.5
```
This adds a 0.5-second delay between task submissions.

#### Disabling Scoring
```bash
actbench run --agent raccoonai --all-tasks --no-scoring
```
This disables the LLM powered scoring, and gives all tasks a score of -1.

#### Combined Options

You can combine these options for more complex benchmark configurations:

```bash
actbench run --agent raccoonai --agent anotheragent --task 1 --task 2 --random 3 --parallel 2 --rate-limit 0.2
```

This command runs tasks 1 and 2, plus 3 random tasks, using both `raccoonai` and `anotheragent` (assuming API keys are set), with a parallelism of 2 and a rate limit of 0.2 seconds.


### 4. Viewing Results

The `results` command group allows you to manage and view benchmark results.

#### Listing Results

```bash
actbench results list
```

You can filter results by agent or run ID:

```bash
actbench results list --agent raccoonai
actbench results list --run-id <run_id>
```

#### Exporting Results

You can export results to JSON or CSV files:

```bash
actbench results export --format json --output results.json
actbench results export --format csv --output results.csv --agent raccoonai
```



#### Here's a complete table detailing the `actbench` CLI commands, their flags (options) and explanations:

| Command                        | Flag(s) / Option(s)    | Explanation                                                                                                                                           |
|:-------------------------------|:-----------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------|
| `actbench run`                 | `--task` / `-t`        | Specifies one or more task IDs to run.  Can be used multiple times.  If omitted, other task selection flags (`--random`, `--all-tasks`) must be used. |
|                                | `--agent` / `-a`       | Specifies one or more agents to use. Can be used multiple times. If omitted, `--all-agents` must be used.                                             |
|                                | `--random` / `-r`      | Runs a specified number of random tasks.  Takes an integer argument (e.g., `--random 5`).                                                             |
|                                | `--all-tasks`          | Runs all available tasks.                                                                                                                             |
|                                | `--all-agents`         | Runs with all configured agents (for which API keys have been set).                                                                                   |
|                                | `--parallel` / `-p`    | Sets the number of tasks to run concurrently. Takes an integer argument (e.g., `--parallel 4`).  Defaults to 1 (no parallelism).                      |
|                                | `--rate-limit` / `-l`  | Sets the delay (in seconds) between task submissions.  Takes a float argument (e.g., `--rate-limit 0.5`). Defaults to 0.1.                            |
|                                | `--no-scoring` / `-ns` | Disables LLM-based scoring. Results will have a score of -1.                                                                                          |
| `actbench tasks list`          | *None*                 | Lists all available tasks in the dataset, showing their ID, query, URL, complexity, and whether they require login.                                   |
| `actbench set-key`             | `--agent` / `-a`       | Sets the API key for a specified agent.  Prompts the user to enter the key securely.  Example: `actbench set-key --agent raccoonai`                   |
| `actbench agents list`         | *None*                 | Lists all supported agents, and shows which agents have API Keys stored.                                                                              |
| `actbench results list`        | `--agent` / `-a`       | Filters the results to show only those for a specific agent.                                                                                          |
|                                | `--run-id` / `-r`      | Filters the results to show only those for a specific run ID.                                                                                         |
| `actbench results export`      | `--agent` / `-a`       | Filters the results to be exported to a specific agent.                                                                                               |
|                                | `--run-id` / `-r`      | Filters the results to be exported for a specific run ID.                                                                                             |
|                                | `--format` / `-f`      | Specifies the export format.  Must be one of `json` or `csv`. Defaults to `json`.                                                                     |
|                                | `--output` / `-o`      | Specifies the output file path.  Required.                                                                                                            |
| `actbench`                     | *None*                 | Prints the help message for the CLI.                                                                                                                  |
| `actbench --version`           | *None*                 | Prints the actbench version number.                                                                                                                   |


## Extending actbench

### Adding New Agents

1.  **Create a new client class:**  Create a new Python file in the `actbench/clients/` directory (e.g., `my_agent.py`).
2.  **Implement the `BaseClient` interface:**  Your class should inherit from `actbench.clients.BaseClient` and implement the `set_api_key()` and `run()` methods.
3.  **Register your client:**  Add your client class to the `_CLIENT_REGISTRY` in `actbench/clients/__init__.py`.

### Adding New Datasets

1.  **Create a new dataset class:** Create a new Python file in the `actbench/datasets/` directory (e.g., `my_dataset.py`).
2.  **Implement the `BaseDataset` interface:** Your class should inherit from `actbench.datasets.BaseDataset` and implement the `load_task_data()`, `get_all_task_ids()`, and `get_all_tasks()` methods.
3.  **Provide your dataset file:**  Place your dataset file (e.g., `my_dataset.jsonl`) in the `src/actbench/dataset/` directory.
4.  **Update `_DATASET_INSTANCE`**: If you want to use this dataset by default, update the `_DATASET_INSTANCE` variable in `src/actbench/datasets/__init__.py`.

### Adding New Evaluation Metrics

You can customize the evaluation process by modifying the `Evaluator` class in `actbench/executor/evaluator.py` or by creating a new evaluator and integrating it into the `TaskExecutor`.

## Contributing

Contributions are welcome! Please follow these simple guidelines:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Write clear and concise code with appropriate comments.
4.  Submit a pull request.
