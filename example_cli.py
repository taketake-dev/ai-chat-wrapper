import os
import sys

from dotenv import load_dotenv
from ai_service.factory import AIServiceFactory


def main() -> None:
    load_dotenv()
    provider = os.getenv("AI_PROVIDER", "gemini")
    api_key = os.getenv("GEMINI_API_KEY")
    system_instruction = os.getenv("SYSTEM_INSTRUCTION")

    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        prompt = input("Prompt: ").strip()

    if not prompt:
        print("No prompt provided.")
        raise SystemExit(1)

    ai_assistant = AIServiceFactory.create_service(provider=provider, api_key=api_key)
    response = ai_assistant.send_message(
        prompt=prompt,
        system_instruction=system_instruction,
    )
    print(response.text)


if __name__ == "__main__":
    main()
