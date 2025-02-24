from typing import Dict, Any, List
from .task_executor import TaskExecutor
from ..datasets import load_task_data, get_all_task_ids


class BenchmarkRunner:
    """Handles the execution of the entire benchmark."""

    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.task_ids = get_all_task_ids()

    def run(self) -> List[Dict[str, Any]]:
        """Runs all tasks for all agents and returns all results."""
        all_results = []
        for task_id in self.task_ids:
            task_data = load_task_data(task_id)
            for agent_name in self.api_keys:
                executor = TaskExecutor(agent_name, self.api_keys, task_data)
                result = executor.run()
                all_results.append(result)
        return all_results
