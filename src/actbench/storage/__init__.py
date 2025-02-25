import json
import os
import time
from typing import List, Dict, Any, Optional

KEYS_FILE = "keys.json"
RESULTS_DIR = "results"


def _ensure_storage():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "w") as f:
            json.dump({}, f)


def _load_keys() -> Dict[str, str]:
    _ensure_storage()
    with open(KEYS_FILE, "r") as f:
        return json.load(f)


def _save_keys(keys: Dict[str, str]) -> None:
    _ensure_storage()
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)


def _get_results_file(run_id: str, agent: str) -> str:
    agent_dir = os.path.join(RESULTS_DIR, run_id)
    os.makedirs(agent_dir, exist_ok=True)
    return os.path.join(agent_dir, f"{agent}.json")


def insert_result(task_id: str, agent: str, success: bool, latency_ms: int, run_id: str,
                  response: Optional[str] = None, score: int = 0) -> None:
    _ensure_storage()
    result_file = _get_results_file(run_id, agent)

    if os.path.exists(result_file):
        with open(result_file, "r") as f:
            results = json.load(f)
    else:
        results = []

    new_result = {
        "task_id": task_id,
        "agent": agent,
        "success": success,
        "latency_ms": latency_ms,
        "response": response,
        "timestamp": int(time.time() * 1000),
        "score": score,
        "run_id": run_id,
    }
    results.append(new_result)

    with open(result_file, "w") as f:
        json.dump(results, f, indent=2)


def get_all_results() -> List[Dict[str, Any]]:
    _ensure_storage()
    all_results = []
    for run_id in os.listdir(RESULTS_DIR):
        run_dir = os.path.join(RESULTS_DIR, run_id)
        if os.path.isdir(run_dir):
            for agent_file in os.listdir(run_dir):
                if agent_file.endswith(".json"):
                    filepath = os.path.join(run_dir, agent_file)
                    with open(filepath, "r") as f:
                        try:
                            results = json.load(f)
                            all_results.extend(results)
                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode JSON in {filepath}")
    return all_results


def get_results_by_agent(agent: str) -> List[Dict[str, Any]]:
    all_results = get_all_results()
    return [result for result in all_results if result["agent"] == agent]


def get_results_by_run_id(run_id: str) -> List[Dict[str, Any]]:
    all_results = get_all_results()
    return [result for result in all_results if result["run_id"] == run_id]


def insert_api_key(agent: str, key: str) -> None:
    keys = _load_keys()
    keys[agent] = key
    _save_keys(keys)


def get_api_key(agent: str) -> Optional[str]:
    keys = _load_keys()
    return keys.get(agent)


def get_all_api_keys() -> Dict[str, str]:
    return _load_keys()


_ensure_storage()
