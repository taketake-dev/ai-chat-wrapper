# AI サービスパッケージ：外部インターフェース仕様書

本ドキュメントは、複数のAIプロバイダー（Gemini、OpenAI等）を統一されたチャットインターフェースで利用するためのパッケージ設計書である。開発者は本仕様に基づき、各クラスおよびメソッドを実装すること。

---

## 1. 全体構造（クラス関係図）

使う側からは `AIServiceFactory` と `AIService` のみが公開API（外部インターフェース）として見え、実際の各AIとの通信は `BaseAIClient` を継承した個別クライアントが隠蔽（カプセル化）された状態で担当する。

注意: リポジトリ内の既存コードは古い設計や未実装の箇所が含まれる想定です。本仕様が最新版です。実装はすべて本 `SPEC.md` の仕様に書き換えることを前提としてください。

---

## 2. 最外殻：生成ロジック（Factory）

使う側が最初にアクセスする窓口となるクラス。インスタンス化の複雑な条件分岐や、デフォルト値の割り当て、環境変数の読み込みをこの中で一元管理する。

### `AIServiceFactory` クラス

#### `create_service` (静的メソッド)

- **役割：** 指定されたプロバイダーに応じた内部クライアントを組み立て、`AIService` のインスタンスを生成して返す。
- **引数：**
  - `provider` (str, 必須): 接続するAIサービス名（`"gemini"` または `"openai"`）。
  - `api_key` (str | None, 既定値: `None`): 明示的なAPIキー。省略された場合は環境変数（`GEMINI_API_KEY` または `OPENAI_API_KEY`）から自動取得する。
  - `model` (str | None, 既定値: `None`): モデル名。省略された場合は各プロバイダーのデフォルトモデル（Gemini: `gemini-2.5-flash` / OpenAI: `gpt-4o`）を自動選択する。
  - `timeout` (int, 既定値: `30`): 通信のタイムアウト秒数。
  - `history` (list[dict[str, str]] | None, 既定値: `None`): 過去の会話ログの初期値。
- **戻り値：** `AIService`（初期化済みのインスタンス）

---

## 3. 最外殻：サービス本体（Chatオブジェクト）

使う側がメッセージの送受信を行うメインのオブジェクト。このオブジェクト自体が会話のコンテキスト（履歴）を保持する「ステートフル（状態を持つ）」な設計とする。

### `AIService` クラス

#### `__init__` (コンストラクタ)

- **役割：** Factoryまたは上級ユーザーから渡された部品をセットし、履歴を初期化する。
- **引数：**
  - `client` (BaseAIClient, 必須): 抽象クラスを満たした個別クライアントの実体。
  - `timeout` (int, 既定値: `30`): タイムアウト秒数。
  - `history` (list[dict[str, str]] | None, 既定値: `None`): 初期履歴。渡された場合は `self.history` に格納し、渡されなかった場合は空のリスト `[]` で初期化する。

  - 追加要件: `AIService` は履歴操作用に `reset_history()` を公開すること。`reset_history()` は `self.history` を空のリストに戻し、履歴に関するトークン累積や内部カウンターも初期化する。

#### `send_message` (公開メソッド)

- **役割：** ユーザーからの新しいメッセージを受け取り、過去の履歴と合わせてAIに送信し、返答を受け取る。受け取った返答は自身の履歴に自動で追加する。
- **引数：**
  - `prompt` (str, 必須): ユーザーが入力する質問や指示。
  - `system_instruction` (str | None, 既定値: `None`): AIに対する役割定義やシステム指示。
- **戻り値：** `ChatResult`（AIからの返答テキストと消費トークン量等のメタを含むオブジェクト）。詳細は下記「`ChatResult` 仕様」を参照。
- **内部挙動：**
  1. `system_instruction` が指定されている場合、送信用のメッセージ群の先頭に `{"role": "system", "content": system_instruction}` を一時的に追加する。
  2. ユーザーの入力を `{"role": "user", "content": prompt}` として `self.history` に追加（アペンド）する。
  3. 履歴全体を保持した状態で、内部の `self._client.chat(messages=self.history)` を呼び出す。
  4. AIからの返答を `{"role": "assistant", "content": response_text}` として `self.history` に追加する。
  5. `response_text` を戻り値の `ChatResult.text` に設定し、`ChatResult.usage` に消費トークンを含めて返す。

---

## 4. 低いレイヤー：個別クライアントの共通ルール（抽象クラス）

すべての個別AIクライアントが満たすべき契約を定義する。これにより最外殻の `AIService` は相手の正体を知らずに同じメソッドを呼び出すことができる（ポリモーフィズムの実現）。

### `BaseAIClient` クラス (ABCを継承した抽象クラス)

#### `chat` (抽象メソッド / `@abstractmethod`)

- **役割：** 渡されたメッセージ履歴のリストをそのまま各AIのSDKに適した形式に変換し、通信を行う。
- **引数：**
  - `messages` (list[dict[str, str]], 必須): `role` 和 `content` を持つ辞書のリスト。
- **戻り値：** `str`（AIからの返答テキスト）
- **戻り値：** `ChatResult`（`text` と `usage` 等を持つ構造体）。クライアント実装は SDK/HTTP レスポンスから `ChatResult` を組み立てて返すこと。

---

## 5. 低いレイヤー：個別クライアント実装

`BaseAIClient` の契約（`chat` メソッド）を正しくオーバーライドして、本物のSDKを操作する具象クラス。

### `GeminiClient` クラス / `OpenAIClient` クラス

- **役割：** 抽象クラス `BaseAIClient` を継承し、それぞれの公式SDKを使って実際のAPI通信を行う。
- **実装義務：** `chat` メソッドをオーバーライドし、引数で渡されたメッセージ履歴をそれぞれのAPI仕様（Google GenAI SDK や OpenAI Python SDK）に合わせて送信・パースする。

注: `chat` の戻り値は単なる文字列ではなく `ChatResult` を返すこと。`ChatResult` には少なくとも `text`（アシスタント応答）と `usage`（`prompt_tokens`, `completion_tokens`, `total_tokens` などの辞書）を含め、可能であれば `raw`（元レスポンス）や `model` を含めること。

クライアント実装は SDK のレスポンスから `usage` を取得できない場合でも `usage` を `None` または空辞書として返すことができるようにする。

---

## 使う側から見たユースケース（README用サンプルコード）

```python
from ai_chat_wrapper.factory import AIServiceFactory

# ケース1：通常の1往復の会話

chat = AIServiceFactory.create_service(provider="gemini")
reply1 = chat.send_message("こんにちは！")

# ケース2：そのまま連続して会話を続ける（文脈が維持される）

reply2 = chat.send_message("先ほどの挨拶を英語に翻訳して。")

# ケース3：過去のログを初期値として引き継いで再開する

past_logs = [
{"role": "user", "content": "私の名前はタケです。"},
{"role": "assistant", "content": "お疲れ様です、タケさん。"},
]
existing_chat = AIServiceFactory.create_service(provider="gemini", history=past_logs)
reply3 = existing_chat.send_message("私の名前は何でしたか？")
```

---

## ChatResult フィールド定義

以下を Python の `dataclass` として定義し、個別クライアントの `chat()` メソッドおよび `AIService.send_message()` の戻り値として使用すること。

```python
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class ChatResult:
  text: str
  usage: Dict[str, int]  # keys: "prompt_tokens", "completion_tokens", "total_tokens"
  model: str
  latency_ms: int
  raw: Any
```

- `text` (str): AIの生成した返答テキスト本体。
- `usage` (dict[str, int]): トークン消費量。キーは `"prompt_tokens"`, `"completion_tokens"`, `"total_tokens"` で統一すること。取得できない場合は空辞書を返す。
- `model` (str): 実際に実行されたモデル名。
- `latency_ms` (int): API呼び出しの実行時間（ミリ秒）。計測不能な場合は `0` を許容する。
- `raw` (Any): 公式SDKから返された生のレスポンスオブジェクト（デバッグやロギング用）。

クライアント実装と `AIService` はこの `ChatResult` を返すことを契約とする。`AIService.send_message()` は `ChatResult` を受け取り、`self.history` には `{"role": "assistant", "content": ChatResult.text, "tokens": ChatResult.usage.get("completion_tokens")}` のように適宜格納すること。
