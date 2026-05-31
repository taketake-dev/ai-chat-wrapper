"""共通のインターフェース"""

from abc import ABC, abstractmethod
from typing import List

from .types import ChatResult, Message


class AIClientError(Exception):
    """共通の AI クライアント例外。"""


class BaseAIClient(ABC):
    """AI クライアントの共通インターフェース。"""

    def __init__(self, model: str, timeout: int = 30) -> None:
        self.model = model
        self.timeout = timeout

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> ChatResult:
        """単純なテキスト生成を呼び出す。戻り値は `ChatResult` を返すこと。"""

    @abstractmethod
    def chat(self, messages: List[Message], **kwargs) -> ChatResult:
        """チャット形式のやりとりを呼び出す。戻り値は `ChatResult` を返すこと。"""
