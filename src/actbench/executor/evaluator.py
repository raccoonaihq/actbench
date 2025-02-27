import json
import logging
from typing import Dict, Any, Union

from langchain import hub
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI


class Evaluator:
    """Evaluates the agent's response and calculates the final score."""

    def __init__(self, api_key: str = None, model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        self.llm = ChatOpenAI(openai_api_key=api_key, model_name=model_name, temperature=temperature)
        self.prompt_template = hub.pull("raccoonai/actbench-llm-eval-prompt")

    def _get_llm_score(self, query: str, complexity: str, requires_login: bool,
                       response: Union[str, Dict[str, Any]]) -> float:
        chain = self.prompt_template | self.llm | JsonOutputParser()
        try:
            llm_response = chain.invoke(
                input={
                    "query": query,
                    "response": json.dumps(response) if isinstance(response, dict) else response,
                    "complexity": complexity,
                    "requires_login": requires_login
                }
            )
            avg_llm_score = (
                    (llm_response["relevance"] + llm_response["completeness"] + llm_response["helpfulness"]) / 3 * 10
            )
            return avg_llm_score
        except Exception as e:
            logging.error(f"LLM evaluation failed: {e}")
            return 0.0

    def calculate_score(self, query: str, complexity: str, requires_login: bool, response: Union[str, Dict[str, Any]],
                        success: bool) -> int:
        if not success:
            return 0

        return int(self._get_llm_score(query, complexity, requires_login, response))
