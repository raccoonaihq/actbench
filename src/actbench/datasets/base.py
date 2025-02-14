from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseDataset(ABC):
    @abstractmethod
    def load_task_data(self, task_type: str, category: str, task_id: str) -> Dict[str, Any]:
        """Loads data for a specific task."""
        pass

    @abstractmethod
    def get_available_categories(self) -> List[str]:
        """Returns a list of available categories."""
        pass

    @abstractmethod
    def get_task_ids_by_category(self, category: str) -> List[str]:
        """Returns a list of task IDs within a category."""
        pass
