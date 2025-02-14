import os
from typing import Dict, Any, List

from .base import BaseDataset
from .json import JsonDataset

_DATASET_INSTANCE: BaseDataset = JsonDataset(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset')
)


def load_task_data(task_type: str, category: str, task_id: str) -> Dict[str, Any]:
    return _DATASET_INSTANCE.load_task_data(task_type, category, task_id)


def get_available_categories() -> List[str]:
    return _DATASET_INSTANCE.get_available_categories()


def get_task_ids_by_category(category: str) -> List[str]:
    return _DATASET_INSTANCE.get_task_ids_by_category(category)
