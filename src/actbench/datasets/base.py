from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseDataset(ABC):
    @abstractmethod
    def load_task_data(self, task_id: str | int) -> Dict[str, Any]:
        """Loads data for a specific task."""
        pass

    @abstractmethod
    def get_all_task_ids(self) -> List[str]:
        """Returns a list of all available task IDs."""
        pass

    @abstractmethod
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Returns a list of all available tasks."""
        pass
