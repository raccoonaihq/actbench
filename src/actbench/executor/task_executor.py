from typing import Dict, Any

from .evaluator import Evaluator
from ..clients import get_agent_client, BaseClient
from ..storage import insert_result


class TaskExecutor:
    """Handles the execution of a single task."""

    def __init__(self, agent_name: str, api_keys: Dict[str, str], task_data: Dict[str, Any], run_id: str,
                 no_scoring: bool):
        self.agent_name = agent_name
        self.api_keys = api_keys
        self.task_data = task_data
        self.run_id = run_id
        self.no_scoring = no_scoring
        self.agent = self._get_agent()

    def _get_agent(self) -> BaseClient:
        """Gets the agent client and sets the API key."""
        client = get_agent_client(self.agent_name)
        client.set_api_key(self.api_keys[self.agent_name])
        return client

    def run(self) -> Dict[str, Any]:
        """Executes the task and returns the result."""
        try:
            result = self.agent.run(self.task_data)

            if self.no_scoring:
                score = -1
            else:
                evaluator = Evaluator(self.api_keys['openai'])
                score = evaluator.calculate_score(self.task_data['query'], self.task_data['complexity'],
                                                  self.task_data['requires_login'], result.get('response'),
                                                  result['success'])

            insert_result(str(self.task_data['task_id']), self.agent_name, result['success'],
                          result.get('latency_ms', -1), self.run_id, result.get('response'), score)
            return result
        except Exception as e:
            insert_result(str(self.task_data['task_id']), self.agent_name, False, -1, self.run_id, str(e))
            return {"success": False, "error": str(e)}
