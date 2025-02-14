from typing import Dict, Any
from ..clients import get_agent_client, BaseClient
from ..database import insert_result


class TaskExecutor:
    """Handles the execution of a single task."""

    def __init__(self, agent_name: str, api_keys: Dict[str, str], task_data: Dict[str, Any], task_type: str):
        self.agent_name = agent_name
        self.api_keys = api_keys
        self.task_data = task_data
        self.task_type = task_type
        self.agent = self._get_agent()  # Get agent *after* setting attributes

    def _get_agent(self) -> BaseClient:
        """Gets the agent client and sets the API key."""
        client = get_agent_client(self.agent_name)
        client.set_api_key(self.api_keys[self.agent_name])
        return client

    def run(self) -> Dict[str, Any]:
        """Executes the task and returns the result."""
        try:
            if self.task_type == "run":
                result = self.agent.run(self.task_data)
            elif self.task_type == "extract":
                result = self.agent.extract(self.task_data)
            else:
                raise ValueError(f"Invalid task_type: {self.task_type}")

            insert_result(self.task_data['task_id'], self.agent_name, result['success'],
                          result.get('latency_ms', -1), result.get('error'))
            return result
        except Exception as e:
            insert_result(self.task_data['task_id'], self.agent_name, False, -1, str(e))
            return {"success": False, "error": str(e)}
