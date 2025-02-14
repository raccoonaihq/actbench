from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class BaseResult(BaseModel):
    task_id: str
    agent: str
    timestamp: int
    success: bool
    latency_ms: int
    error: Optional[str] = None


class RunResult(BaseResult):
    response: Dict[str, Any]


class ExtractResult(BaseResult):
    response: Dict[str, Any]
