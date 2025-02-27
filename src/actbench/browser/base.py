from abc import ABC, abstractmethod


class BaseBrowser(ABC):

    @abstractmethod
    def get_cdp_url(self, url: str) -> str:
        pass

    @abstractmethod
    def terminate(self):
        pass
