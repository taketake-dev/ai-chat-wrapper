# ai-service

Gemini を統一インターフェースで扱うための Python パッケージです。

現時点では Gemini のみ実装済みです。OpenAI は仕様上の将来拡張対象ですが、実装はまだありません。

## できること

- `AIServiceFactory.create_service()` で会話サービスを生成する
- `AIService.send_message()` で会話を継続する
- `AIService.reset_history()` で会話履歴を初期化する
- `ChatResult` で返答テキストとトークン使用量を受け取る

## 使い方

```python
from ai_service.factory import AIServiceFactory

chat = AIServiceFactory.create_service(provider="gemini")
result = chat.send_message("こんにちは！")

print(result.text)
print(result.usage)
print(result.model)
```

### 継続会話

`AIService` は履歴を保持します。連続して `send_message()` を呼ぶと、その前の会話文脈を引き継ぎます。

```python
from ai_service.factory import AIServiceFactory

chat = AIServiceFactory.create_service(provider="gemini")
chat.send_message("私の名前はタケです。")
result = chat.send_message("私の名前は何でしたか？")

print(result.text)
```

### 履歴をリセットする

```python
from ai_service.factory import AIServiceFactory

chat = AIServiceFactory.create_service(provider="gemini")
chat.send_message("最初の会話です。")
chat.reset_history()
result = chat.send_message("最初からやり直します。")

print(result.text)
```

## 戻り値

`send_message()` と個別クライアントの `chat()` は `ChatResult` を返します。

- `text`: AI の返答テキスト
- `usage`: `prompt_tokens`, `completion_tokens`, `total_tokens`
- `model`: 実行されたモデル名
- `latency_ms`: 応答時間（ミリ秒）
- `raw`: SDK または HTTP レスポンスの生データ

## 環境変数

- `GEMINI_API_KEY`: Gemini API キー
- `SYSTEM_INSTRUCTION`: `example_cli.py` のデモ実行時に使う system 指示

サンプル用の `.env.example` を同梱しています。ルートにコピーして環境に合わせて編集してください:

```bash
cp .env.example .env
```

サンプルスクリプト: このリポジトリには `example_cli.py`（デモ用の簡易CLI）が含まれています。README のデモ実行例はこのファイルを使ったものです。

## デモ実行

```bash
python example_cli.py "こんにちは"
```

## 注意

現在このパッケージは PyPI（pip）には登録されていません。手動でのインストールは `pip install -e .` などの方法をお使いください。
