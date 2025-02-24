from .base import BaseClient
from typing import Dict, Any
import time
from raccoonai import RaccoonAI
from raccoonai.types import lam_run_params


class RaccoonAIClient(BaseClient):
    def __init__(self):
        self.api_key = None
        self.client = None

    def set_api_key(self, api_key: str) -> None:
        self.api_key = api_key
        if self.client is None:
            self.client = RaccoonAI(secret_key=self.api_key)

    def run(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "task_id": task_data['task_id'],
                "agent": "raccoonai",
                "latency_ms": -1,
                "success": False,
                "response": "API key not set"
            }
        if self.client is None:
            return {
                "task_id": task_data['task_id'],
                "agent": "raccoonai",
                "latency_ms": -1,
                "success": False,
                "response": "Raccoon AI client is not initialized"
            }

        start_time = time.time()
        try:
            response = self.client.lam.run(
                query=task_data["query"],
                raccoon_passcode=task_data.get("passcode", "default_test"),
                app_url=task_data["url"],
                stream=False,
                advanced=lam_run_params.Advanced(
                    block_ads=True,
                    solve_captchas=True,
                )
            )
            end_time = time.time()
        except Exception as e:
            return {
                "task_id": task_data['task_id'],
                "agent": "raccoonai",
                "latency_ms": -1,
                "success": False,
                "response": str(e)
            }

        return {
            "task_id": task_data['task_id'],
            "agent": "raccoonai",
            "latency_ms": int((end_time - start_time) * 1000),
            "success": response.task_status == 'DONE',
            "response": response.model_dump()
        }
