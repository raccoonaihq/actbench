import json
from typing import Dict, Any, List
from .base import BaseDataset


class JsonDataset(BaseDataset):
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path

    def load_task_data(self, task_id: str | int) -> Dict[str, Any]:
        try:
            with open(self.dataset_path, 'r') as f:
                for line in f:
                    task = json.loads(line)
                    if task["task_id"] == task_id:
                        return task
                raise KeyError(f"Task ID '{task_id}' not found in '{self.dataset_path}'")
        except FileNotFoundError:
            raise FileNotFoundError(f"Dataset file not found: {self.dataset_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in dataset file: {self.dataset_path}")

    def get_all_task_ids(self) -> List[str]:
        task_ids = []
        try:
            with open(self.dataset_path, 'r') as f:
                for line in f:
                    task = json.loads(line)
                    task_ids.append(task["task_id"])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        return task_ids

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        tasks = []
        try:
            with open(self.dataset_path, 'r') as f:
                for line in f:
                    task = json.loads(line)
                    tasks.append(task)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        return tasks
