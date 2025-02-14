from .base import BaseClient
from .raccoonai import RaccoonAIClient

_CLIENT_REGISTRY = {
    "raccoonai": RaccoonAIClient,
}


def get_agent_client(agent_name: str) -> BaseClient:
    client_class = _CLIENT_REGISTRY.get(agent_name.lower())
    if client_class is None:
        raise ValueError(f"Unsupported agent: {agent_name}")
    return client_class()
