from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..browser import BaseBrowser


class BaseClient(ABC):
    @abstractmethod
    def set_api_key(self, api_key: str) -> None:
        pass

    @abstractmethod
    def run(self, task_data: Dict[str, Any], browser: Optional[BaseBrowser] = None) -> Dict[str, Any]:
        pass

