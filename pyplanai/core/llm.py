from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib import response

from groq import Groq
from .config import GROQ_API_KEY as DEFAULT_GROQ_API_KEY

PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"
DEFAULT_MODEL = "openai/gpt-oss-120b"


class LLMError(RuntimeError):
    pass

class GroqPlannerClient:
    def __init__(self, api_key: str | None = None):
        if api_key is None:
            api_key = DEFAULT_GROQ_API_KEY
            if api_key is None:
                raise LLMError("GROQ_API_KEY not set in environment or .env file.")
        self.client = Groq(api_key=api_key)
        self.model = DEFAULT_MODEL
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def generate_blueprint(self, date_str: str, tasks: list[dict], max_retries: int = 2) -> list[dict]:
        user_payload = json.dumps({"date": date_str, "tasks": tasks})
        last_error = None
        for attempt in range(max_retries + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_payload},
                ],
                temperature=0.6,
                max_completion_tokens=8192,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw.removeprefix("```json")
            elif raw.startswith("```"):
                raw = raw.removeprefix("```")
            raw = raw.removesuffix("```").strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(1)
                    continue
        raise LLMError(f"Failed to parse JSON response after {max_retries + 1} attempts: {last_error}")