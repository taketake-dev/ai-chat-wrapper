"""Gemini 用クライアント"""

from .base_client import AIClientError, BaseAIClient


class GeminiClient(BaseAIClient):
    """Gemini 用クライアント。実装予定。"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.0",
        timeout: int = 30,
    ) -> None:
        super().__init__(model=model, timeout=timeout)
        self.api_key = api_key

    def complete(self, prompt: str, **kwargs) -> str:
        raise AIClientError("Gemini client is not implemented yet.")

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        raise AIClientError("Gemini client is not implemented yet.")
