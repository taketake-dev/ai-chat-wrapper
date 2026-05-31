import pathlib
import sys
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_service.factory import AIService
from ai_service.types import ChatResult, Message


class DummyClient:
    def __init__(self) -> None:
        self.calls = []

    def chat(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return ChatResult(
            text="dummy response",
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            model="dummy-model",
            latency_ms=12,
            raw={"ok": True},
        )


class AIServiceTestCase(unittest.TestCase):
    def test_send_message_appends_history_and_returns_chat_result(self) -> None:
        client = DummyClient()
        service = AIService(client=client)

        result = service.send_message("hello")

        self.assertIsInstance(result, ChatResult)
        self.assertEqual(result.text, "dummy response")
        self.assertEqual(len(service.history), 2)
        self.assertEqual(service.history[0], Message(role="user", content="hello", tokens=None))
        self.assertEqual(service.history[1].role, "assistant")
        self.assertEqual(service.history[1].content, "dummy response")
        self.assertEqual(service.history[1].tokens, 1)
        self.assertEqual(len(client.calls), 1)

    def test_reset_history_clears_history(self) -> None:
        client = DummyClient()
        service = AIService(client=client)

        service.send_message("hello")
        service.reset_history()

        self.assertEqual(service.history, [])

    def test_max_history_tokens_trims_old_messages(self) -> None:
        client = DummyClient()
        service = AIService(client=client, max_history_tokens=2)

        service.send_message("first")
        service.send_message("second")

        self.assertGreaterEqual(len(service.history), 1)
        self.assertLessEqual(service._history_token_total(), 2)


if __name__ == "__main__":
    unittest.main()
