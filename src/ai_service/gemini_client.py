"""Gemini 用クライアント"""

from .base_client import AIClientError, BaseAIClient
from .types import Message, ChatResult
from typing import List


class GeminiClient(BaseAIClient):
    """Gemini 用クライアント。実装予定。

    NOTE: メソッドシグネチャは SPEC に合わせて `Message` / `ChatResult` を使う。
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.0",
        timeout: int = 30,
    ) -> None:
        super().__init__(model=model, timeout=timeout)
        self.api_key = api_key

    def complete(self, prompt: str, **kwargs) -> ChatResult:
        raise AIClientError("Gemini client is not implemented yet.")

    def chat(self, messages: List[Message], **kwargs) -> ChatResult:
        raise AIClientError("Gemini client is not implemented yet.")
