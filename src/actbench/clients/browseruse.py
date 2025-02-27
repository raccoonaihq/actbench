import asyncio
import os
import time
from typing import Dict, Any

from browser_use import Agent
from langchain_openai import ChatOpenAI

from .base import BaseClient


class BrowserUseClient(BaseClient):
    def __init__(self):
        os.environ["ANONYMIZED_TELEMETRY"] = "false"
        self.api_key = None
        self.client = None

    def set_api_key(self, api_key: str) -> None:
        self.api_key = api_key

    def run(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "task_id": task_data["task_id"],
                "agent": "browseruse",
                "latency_ms": -1,
                "success": False,
                "response": "OpenAI API key not set"
            }

        start_time = time.time()

        try:
            agent = Agent(
                task=task_data["query"],
                llm=ChatOpenAI(api_key=self.api_key, model="gpt-4o"),
                generate_gif=False,
            )

            result = asyncio.run(agent.run(20))
            result_json = result.model_dump()
            history = result_json.get("history", [])
            last_history = history[-1]
            result_list = last_history.get("result", [])
            final_response = result_list[-1]

            success = final_response.get("is_done", False)
            response_message = final_response.get("extracted_content", "No response message provided.")
            end_time = time.time()
        except Exception as e:
            return {
                "task_id": task_data["task_id"],
                "agent": "browseruse",
                "latency_ms": -1,
                "success": False,
                "response": f"Unexpected error: {str(e)}",
            }

        return {
            "task_id": task_data["task_id"],
            "agent": "browseruse",
            "latency_ms": int((end_time - start_time) * 1000),
            "success": success,
            "response": response_message,
        }
