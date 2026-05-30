"""共通のインターフェース"""

from abc import ABC, abstractmethod


class AIClientError(Exception):
    """共通の AI クライアント例外。"""


class BaseAIClient(ABC):
    """AI クライアントの共通インターフェース。"""

    def __init__(self, model: str, timeout: int = 30) -> None:
        self.model = model
        self.timeout = timeout

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """単純なテキスト生成を呼び出す。"""

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """チャット形式のやりとりを呼び出す。"""
