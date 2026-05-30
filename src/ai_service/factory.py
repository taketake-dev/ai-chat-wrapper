import os
from typing import Any

from .base_client import BaseAIClient
from .gemini_client import GeminiClient
from .openai_client import OpenAIClient

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "chatgpt": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
}


def create_client(provider: str = "openai", **kwargs: Any) -> BaseAIClient:
    """指定されたプロバイダーの AI クライアントを生成する。"""
    provider_key = provider.strip().lower()
    if provider_key in {"openai", "chatgpt"}:
        return OpenAIClient(**kwargs)
    if provider_key in {"gemini", "google", "bard"}:
        client_kwargs = {k: v for k, v in kwargs.items() if k in {"api_key", "model", "timeout"}}
        return GeminiClient(**client_kwargs)

    raise ValueError(f"Unsupported AI provider: {provider}")


class AIService:
    """呼び出し側が使う AI サービスのラッパー。"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 30,
        organization: str | None = None,
    ) -> None:
        self.provider = provider.strip().lower()
        self.model = model or DEFAULT_MODELS.get(self.provider, DEFAULT_MODELS["openai"])

        if self.provider in {"gemini", "google", "bard"}:
            api_key = api_key or os.getenv("GEMINI_API_KEY")
        else:
            api_key = api_key or os.getenv("OPENAI_API_KEY")

        organization = organization or os.getenv("OPENAI_ORGANIZATION")
        self._client = create_client(
            provider=self.provider,
            api_key=api_key,
            model=self.model,
            timeout=timeout,
            organization=organization,
        )

    def generate_text(self, prompt: str, system_instruction: str | None = None, **kwargs: Any) -> str:
        """テキストを生成する。毎回変わる入力を渡す。"""
        if not prompt:
            raise ValueError("prompt is required")

        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        return self._client.chat(messages=messages, **kwargs)


class AIServiceFactory:
    """AI サービスの生成を提供するファクトリー。"""

    @classmethod
    def create_service(
        cls,
        provider: str = "openai",
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 30,
        organization: str | None = None,
    ) -> AIService:
        return AIService(
            provider=provider,
            api_key=api_key,
            model=model,
            timeout=timeout,
            organization=organization,
        )
