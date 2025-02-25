import logging
import os
from typing import Dict, Any, List

import requests

from .base import BaseDataset
from .json import JsonDataset

DATASET_URL = "https://raw.githubusercontent.com/raccoonaihq/actbench/master/dataset.jsonl"
LOCAL_DATASET_PATH = "dataset.jsonl"


def download_dataset():
    if not os.path.exists(LOCAL_DATASET_PATH):
        response = requests.get(DATASET_URL)
        if response.status_code == 200:
            with open(LOCAL_DATASET_PATH, "w", encoding="utf-8") as file:
                file.write(response.text)
        else:
            logging.error(f"Failed to download dataset: HTTP {response.status_code}")


download_dataset()

_DATASET_INSTANCE: BaseDataset = JsonDataset(LOCAL_DATASET_PATH)


def load_task_data(task_id: str | int) -> Dict[str, Any]:
    return _DATASET_INSTANCE.load_task_data(task_id)


def get_all_task_ids() -> List[str]:
    return _DATASET_INSTANCE.get_all_task_ids()


def get_all_tasks() -> List[Dict[str, Any]]:
    return _DATASET_INSTANCE.get_all_tasks()
