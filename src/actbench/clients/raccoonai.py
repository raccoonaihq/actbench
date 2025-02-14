from .base import BaseClient
from typing import Dict, Any
import time
from raccoonai import RaccoonAI
from raccoonai.types import lam_run_params, lam_extract_params

from ..models import RunResult, ExtractResult


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
            return {"success": False, "error": "API key not set", "latency_ms": 0}
        if self.client is None:
            return {"success": False, "error": "RaccoonAI client is not initialized", "latency_ms": 0}

        start_time = time.time()
        try:
            response = self.client.lam.run(
                query=task_data["query"],
                raccoon_passcode=task_data.get("passcode", "default_test"),
                app_url=task_data["url"],
                stream=False,
                advanced=lam_run_params.Advanced(
                    block_ads=task_data.get("contains_ads", False),
                    solve_captchas=task_data.get("contains_captchas", False),
                )
            )
            end_time = time.time()
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": int((time.time() - start_time) * 1000)}

        return RunResult(
            task_id=task_data['task_id'],
            agent='raccoonai',
            timestamp=int(time.time() * 1000),
            success=response.task_status == 'DONE',
            latency_ms=int((end_time - start_time) * 1000),
            response=response.model_dump(),
        ).model_dump()

    def extract(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "API key not set", "latency_ms": 0}
        if self.client is None:
            return {"success": False, "error": "RaccoonAI client not initialized.", "latency_ms": 0}

        start_time = time.time()

        try:
            response = self.client.lam.extract(
                query=task_data["query"],
                raccoon_passcode=task_data.get("passcode", "default_test"),
                app_url=task_data["url"],
                stream=False,
                schema=task_data["response_schema"],
                max_count=task_data["count"],
                advanced=lam_extract_params.Advanced(
                    block_ads=task_data.get("contains_ads", False),
                    solve_captchas=task_data.get("contains_captchas", False),
                )
            )
            end_time = time.time()

        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": int((time.time() - start_time) * 1000)}

        return ExtractResult(
            task_id=task_data['task_id'],
            agent='raccoonai',
            timestamp=int(time.time() * 1000),
            success=response.task_status == 'DONE',
            latency_ms=int((end_time - start_time) * 1000),
            response=response.model_dump(),
        ).model_dump()
