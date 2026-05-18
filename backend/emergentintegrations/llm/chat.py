"""OpenAI-backed compatibility adapter for legacy LLM chat imports.

The original application imported `LlmChat` and `UserMessage` from the external
Emergent integration package. This local adapter preserves that narrow API
surface while using the official OpenAI SDK already declared in requirements.
"""

import os
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI


@dataclass
class UserMessage:
    text: str


class LlmChat:
    def __init__(self, api_key: Optional[str], session_id: str, system_message: str = ""):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")
        self.session_id = session_id
        self.system_message = system_message
        self.provider = "openai"
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def with_model(self, provider: str, model: str):
        self.provider = provider
        if provider == "openai" and model:
            self.model = os.environ.get("OPENAI_MODEL", model)
        return self

    async def send_message(self, user_message: UserMessage) -> str:
        if self.provider != "openai":
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_message.text},
            ],
        )

        message = response.choices[0].message.content
        return message or ""
