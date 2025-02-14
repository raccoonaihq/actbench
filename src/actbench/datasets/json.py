import json
import os
from typing import Dict, Any, List
from .base import BaseDataset


class JsonDataset(BaseDataset):
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir

    def load_task_data(self, task_type: str, category: str, task_id: str) -> Dict[str, Any]:
        filepath = os.path.join(self.dataset_dir, task_type, f"{category}.json")
        try:
            with open(filepath, 'r') as f:
                tasks = json.load(f)
                for task in tasks:
                    if task["task_id"] == task_id:
                        return task
                raise KeyError(f"Task ID '{task_id}' not found in '{filepath}'")
        except FileNotFoundError:
            raise FileNotFoundError(f"Category file not found: {filepath}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in category file: {filepath}")
        except KeyError:
            raise KeyError(f"Task ID '{task_id}' not found in '{filepath}'")

    def get_available_categories(self) -> List[str]:
        categories = []
        for task_type in ["run", "extract"]:
            type_dir = os.path.join(self.dataset_dir, task_type)
            if os.path.isdir(type_dir):
                for filename in os.listdir(type_dir):
                    if filename.endswith(".json"):
                        categories.append(f"{task_type}/{filename[:-5]}")
        return categories

    def get_task_ids_by_category(self, category: str) -> List[str]:
        task_type, category_name = category.split('/')
        filepath = os.path.join(self.dataset_dir, task_type, f"{category_name}.json")

        try:
            with open(filepath, 'r') as f:
                tasks = json.load(f)
                return [f"{task_type}/{category_name}/{task['task_id']}" for task in tasks]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
