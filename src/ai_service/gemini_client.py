"""Gemini 用クライアント"""

import json
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base_client import AIClientError, BaseAIClient
from .types import ChatResult, Message


class GeminiClient(BaseAIClient):
    """Gemini 用クライアント。

    標準ライブラリの HTTP クライアントを使って Gemini API を呼び出す。
    """

    MAX_RETRIES = 2
    BASE_RETRY_DELAY_SECONDS = 0.5

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        timeout: int = 30,
    ) -> None:
        super().__init__(model=model, timeout=timeout)
        self.api_key = api_key

    def complete(self, prompt: str, **kwargs) -> ChatResult:
        messages = [Message(role="user", content=prompt)]
        return self.chat(messages=messages, **kwargs)

    def chat(self, messages: list[Message], **kwargs) -> ChatResult:
        if not self.api_key:
            raise AIClientError("Gemini API key is required.")

        system_instruction, contents = self._split_messages(messages)
        payload = self._build_payload(contents=contents, system_instruction=system_instruction)
        endpoint = self._build_endpoint()
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        raw: dict[str, object] = {}
        started_at = time.perf_counter()

        for attempt in range(self.MAX_RETRIES + 1):
            request = Request(endpoint, data=body, headers=headers, method="POST")

            try:
                with urlopen(request, timeout=self.timeout) as response:
                    raw_text = response.read().decode("utf-8")
                    raw = json.loads(raw_text) if raw_text else {}
                break
            except HTTPError as error:
                if self._should_retry_http_error(error, attempt):
                    self._sleep_before_retry(attempt)
                    continue

                error_body = error.read().decode("utf-8", errors="replace") if error.fp else ""
                raise AIClientError(
                    f"Gemini API request failed: {error.code} {error.reason} {error_body}"
                ) from error
            except (TimeoutError, socket.timeout, URLError) as error:
                if self._should_retry_network_error(error, attempt):
                    self._sleep_before_retry(attempt)
                    continue

                raise AIClientError(f"Gemini API request failed: {error}") from error
        else:
            raise AIClientError("Gemini API request failed after retries.")

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        text = self._extract_text(raw)
        usage = self._extract_usage(raw)
        raw_model = raw.get("modelVersion")
        model_name = raw_model if isinstance(raw_model, str) else self.model

        return ChatResult(
            text=text,
            usage=usage,
            model=model_name,
            latency_ms=latency_ms,
            raw=raw,
        )

    def _build_endpoint(self) -> str:
        return (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

    def _split_messages(self, messages: list[Message]) -> tuple[str | None, list[dict[str, object]]]:
        system_parts: list[str] = []
        contents: list[dict[str, object]] = []

        for message in messages:
            if message.role == "system":
                system_parts.append(message.content)
                continue

            role = "model" if message.role == "assistant" else "user"
            contents.append(
                {
                    "role": role,
                    "parts": [{"text": message.content}],
                }
            )

        system_instruction = "\n".join(system_parts).strip() or None
        return system_instruction, contents

    def _build_payload(
        self,
        contents: list[dict[str, object]],
        system_instruction: str | None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {"contents": contents}

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        return payload

    def _should_retry_http_error(self, error: HTTPError, attempt: int) -> bool:
        if attempt >= self.MAX_RETRIES:
            return False

        return error.code == 429 or 500 <= error.code < 600

    def _should_retry_network_error(self, error: Exception, attempt: int) -> bool:
        if attempt >= self.MAX_RETRIES:
            return False

        return True

    def _sleep_before_retry(self, attempt: int) -> None:
        delay = self.BASE_RETRY_DELAY_SECONDS * (2**attempt)
        time.sleep(delay)

    def _extract_text(self, raw: dict[str, object]) -> str:
        candidates = raw.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise AIClientError("Gemini API response did not contain candidates.")

        first_candidate = candidates[0]
        if not isinstance(first_candidate, dict):
            raise AIClientError("Gemini API response format is invalid.")

        content = first_candidate.get("content")
        if not isinstance(content, dict):
            raise AIClientError("Gemini API response did not contain content.")

        parts = content.get("parts")
        if not isinstance(parts, list):
            raise AIClientError("Gemini API response did not contain text parts.")

        texts: list[str] = []
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                texts.append(part["text"])

        if not texts:
            raise AIClientError("Gemini API response did not contain text.")

        return "".join(texts)

    def _extract_usage(self, raw: dict[str, object]) -> dict[str, int]:
        usage_metadata = raw.get("usageMetadata")
        if not isinstance(usage_metadata, dict):
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        prompt_tokens = int(usage_metadata.get("promptTokenCount", 0) or 0)
        completion_tokens = int(
            usage_metadata.get("candidatesTokenCount", usage_metadata.get("outputTokenCount", 0)) or 0
        )
        total_tokens = int(usage_metadata.get("totalTokenCount", prompt_tokens + completion_tokens) or 0)

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
