from .base import BaseClient
from .raccoonai import RaccoonAIClient


def get_agent_client(agent_name: str) -> BaseClient:
    from actbench.clients.browseruse import BrowserUseClient
    _CLIENT_REGISTRY = {
        "raccoonai": RaccoonAIClient,
        "browseruse": BrowserUseClient,
    }
    client_class = _CLIENT_REGISTRY.get(agent_name.lower())
    if client_class is None:
        raise ValueError(f"Unsupported agent: {agent_name}")
    return client_class()
