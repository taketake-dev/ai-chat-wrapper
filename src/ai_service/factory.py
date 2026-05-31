import os
from typing import Any

from .base_client import BaseAIClient
from .gemini_client import GeminiClient
from .types import ChatResult, Message

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
}


def create_client(provider: str = "gemini", **kwargs: Any) -> BaseAIClient:
    """指定されたプロバイダーの AI クライアントを生成する。"""
    provider_key = provider.strip().lower()
    if provider_key in {"gemini", "google", "bard"}:
        client_kwargs = {k: v for k, v in kwargs.items() if k in {"api_key", "model", "timeout"}}
        return GeminiClient(**client_kwargs)

    raise NotImplementedError(f"Unsupported AI provider: {provider}")


class AIService:
    """呼び出し側が使う AI サービスのラッパー。"""

    def __init__(
        self,
        client: BaseAIClient,
        timeout: int = 30,
        history: list[Message] | None = None,
        max_history_tokens: int | None = None,
    ) -> None:
        self._client = client
        self.timeout = timeout
        self.history = list(history) if history is not None else []
        self._usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self._turn_count = 0
        self.max_history_tokens = max_history_tokens

    def reset_history(self) -> None:
        """会話履歴と内部カウンターを初期化する。"""
        self.history = []
        self._usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self._turn_count = 0

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0

        estimated = len(text) // 4
        return estimated if estimated > 0 else 1

    def _message_tokens(self, message: Message) -> int:
        if message.tokens is not None:
            return message.tokens

        return self._estimate_tokens(message.content)

    def _history_token_total(self) -> int:
        return sum(self._message_tokens(message) for message in self.history)

    def _trim_history(self) -> None:
        if self.max_history_tokens is None:
            return

        while len(self.history) > 1 and self._history_token_total() > self.max_history_tokens:
            self.history.pop(0)

    def send_message(
        self,
        prompt: str,
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """新しいメッセージを送信し、返答を履歴へ追加する。"""
        if not prompt:
            raise ValueError("prompt is required")

        messages: list[Message] = []
        if system_instruction:
            messages.append(Message(role="system", content=system_instruction))

        user_message = Message(role="user", content=prompt)
        self.history.append(user_message)
        self._trim_history()
        messages.extend(self.history)

        result = self._client.chat(messages=messages, **kwargs)

        assistant_tokens = result.usage.get("completion_tokens")
        self.history.append(Message(role="assistant", content=result.text, tokens=assistant_tokens))
        self._trim_history()

        for key in self._usage_total:
            self._usage_total[key] += result.usage.get(key, 0)

        self._turn_count += 1
        return result

    def generate_text(self, prompt: str, system_instruction: str | None = None, **kwargs: Any) -> ChatResult:
        """後方互換のためのラッパー。"""
        return self.send_message(prompt=prompt, system_instruction=system_instruction, **kwargs)


class AIServiceFactory:
    """AI サービスの生成を提供するファクトリー。"""

    @classmethod
    def create_service(
        cls,
        provider: str = "gemini",
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 30,
        history: list[Message] | None = None,
        max_history_tokens: int | None = None,
    ) -> AIService:
        provider_key = provider.strip().lower()
        if provider_key not in {"gemini", "google", "bard"}:
            raise NotImplementedError(f"Unsupported AI provider: {provider}")

        resolved_model = model or DEFAULT_MODELS["gemini"]
        resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")

        client = create_client(
            provider=provider_key,
            api_key=resolved_api_key,
            model=resolved_model,
            timeout=timeout,
        )

        return AIService(
            client=client,
            timeout=timeout,
            history=history,
            max_history_tokens=max_history_tokens,
        )
