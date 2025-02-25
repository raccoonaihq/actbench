from typing import Dict, Any, List

from .base import BaseDataset
from .json import JsonDataset

_DATASET_INSTANCE: BaseDataset = JsonDataset("./src/dataset/dataset.jsonl")


def load_task_data(task_id: str | int) -> Dict[str, Any]:
    return _DATASET_INSTANCE.load_task_data(task_id)


def get_all_task_ids() -> List[str]:
    return _DATASET_INSTANCE.get_all_task_ids()


def get_all_tasks() -> List[dict[str, Any]]:
    return _DATASET_INSTANCE.get_all_tasks()
