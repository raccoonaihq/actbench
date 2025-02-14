from typing import Dict, Any, List
from .task_executor import TaskExecutor
from ..datasets import load_task_data, get_available_categories, get_task_ids_by_category


class BenchmarkRunner:
    """Handles the execution of the entire benchmark."""

    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.categories = get_available_categories()  # Load once

    def run(self) -> List[Dict[str, Any]]:
        """Runs all tasks for all agents and returns all results."""
        all_results = []
        for category in self.categories:
            task_type, category_name = category.split("/")
            task_ids = get_task_ids_by_category(category)
            for task_id in task_ids:
                _, _, actual_task_id = task_id.split("/")
                task_data = load_task_data(task_type, category_name, actual_task_id)
                for agent_name in self.api_keys:
                    executor = TaskExecutor(agent_name, self.api_keys, task_data, task_type)
                    result = executor.run()
                    all_results.append(result)
        return all_results
