from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseDatabase(ABC):
    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def insert_result(self, task_id: str, agent: str, success: bool, latency_ms: int, run_id: str, response: str = None,
                      score: int = None) -> None:
        pass

    @abstractmethod
    def get_all_results(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def clear_results(self) -> None:
        pass

    @abstractmethod
    def insert_api_key(self, agent: str, key: str) -> None:
        pass

    @abstractmethod
    def get_api_key(self, agent: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_all_api_keys(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def delete_api_key(self, agent: str) -> None:
        pass
