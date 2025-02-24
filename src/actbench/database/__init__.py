from typing import List, Dict, Any, Optional

from .base import BaseDatabase
from .sqlite import SQLiteDatabase

_DB_INSTANCE = SQLiteDatabase()


def get_db() -> BaseDatabase:
    """Returns the database instance."""
    return _DB_INSTANCE


def insert_result(task_id: str, agent: str, success: bool, latency_ms: int, response: str = None) -> None:
    _DB_INSTANCE.insert_result(task_id, agent, success, latency_ms, response)


def get_all_results() -> List[Dict[str, Any]]:
    return _DB_INSTANCE.get_all_results()


def clear_results() -> None:
    _DB_INSTANCE.clear_results()


def insert_api_key(agent: str, key: str) -> None:
    _DB_INSTANCE.insert_api_key(agent, key)


def get_api_key(agent: str) -> Optional[str]:
    return _DB_INSTANCE.get_api_key(agent)


def get_all_api_keys() -> Dict[str, str]:
    return _DB_INSTANCE.get_all_api_keys()


def delete_api_key(agent: str) -> None:
    _DB_INSTANCE.delete_api_key(agent)