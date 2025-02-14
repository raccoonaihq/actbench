from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseClient(ABC):
    @abstractmethod
    def set_api_key(self, api_key: str) -> None:
        pass

    @abstractmethod
    def run(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def extract(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
