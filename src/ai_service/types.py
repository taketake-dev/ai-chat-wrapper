from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Message:
    role: str
    content: str
    tokens: Optional[int] = None


@dataclass
class ChatResult:
    text: str
    usage: Dict[str, int]  # keys: "prompt_tokens", "completion_tokens", "total_tokens"
    model: str
    latency_ms: int
    raw: Any
