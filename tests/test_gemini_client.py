import io
import json
import pathlib
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from email.message import Message as EmailMessage

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_service.base_client import AIClientError
from ai_service.gemini_client import GeminiClient
from ai_service.types import Message as AIMessage


class FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body


class GeminiClientTestCase(unittest.TestCase):
    def test_chat_parses_text_usage_and_model(self) -> None:
        payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "hello world"}],
                    }
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 7,
                "candidatesTokenCount": 5,
                "totalTokenCount": 12,
            },
            "modelVersion": "gemini-2.5-flash",
        }

        fake_response = FakeResponse(json.dumps(payload))

        with patch("ai_service.gemini_client.urlopen", return_value=fake_response), patch(
            "ai_service.gemini_client.time.perf_counter", side_effect=[1.0, 1.2]
        ):
            client = GeminiClient(api_key="test-key", model="gemini-2.5-flash", timeout=10)
            result = client.chat([AIMessage(role="user", content="こんにちは")])

        self.assertEqual(result.text, "hello world")
        self.assertEqual(result.usage, {"prompt_tokens": 7, "completion_tokens": 5, "total_tokens": 12})
        self.assertEqual(result.model, "gemini-2.5-flash")
        self.assertIn(result.latency_ms, {199, 200})
        self.assertEqual(result.raw, payload)

    def test_chat_requires_api_key(self) -> None:
        client = GeminiClient(api_key=None)

        with self.assertRaises(AIClientError):
            client.chat([AIMessage(role="user", content="hello")])

    def test_chat_retries_once_on_http_429(self) -> None:
        payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "retry ok"}],
                    }
                }
            ],
            "usageMetadata": {},
        }

        http_error = HTTPError(
            url="https://example.com",
            code=429,
            msg="Too Many Requests",
            hdrs=EmailMessage(),
            fp=io.BytesIO(b'{"error":"rate limited"}'),
        )

        with patch("ai_service.gemini_client.urlopen", side_effect=[http_error, FakeResponse(json.dumps(payload))]), patch(
            "ai_service.gemini_client.time.perf_counter", side_effect=[1.0, 1.5]
        ), patch("ai_service.gemini_client.time.sleep") as sleep_mock:
            client = GeminiClient(api_key="test-key")
            result = client.chat([AIMessage(role="user", content="こんにちは")])

        self.assertEqual(result.text, "retry ok")
        self.assertEqual(sleep_mock.call_count, 1)
        self.assertEqual(result.usage, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})


if __name__ == "__main__":
    unittest.main()
