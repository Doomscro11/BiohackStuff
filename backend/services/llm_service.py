"""Native LLM service for Peptimancer.

Uses the official OpenAI SDK and keeps provider configuration local to the
application instead of depending on builder-specific integration packages.
"""

import os
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI


DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class UserMessage:
    text: str


class LlmChat:
    """Small async chat wrapper used by peptide-generation code."""

    def __init__(self, api_key: Optional[str] = None, session_id: str = "", system_message: str = ""):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.session_id = session_id
        self.system_message = system_message
        self.provider = "openai"
        self.model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)

    def with_model(self, provider: str, model: str):
        if provider != "openai":
            raise ValueError(f"Unsupported LLM provider: {provider}")
        self.provider = provider
        self.model = os.environ.get("OPENAI_MODEL", model or DEFAULT_MODEL)
        return self

    async def send_message(self, user_message: UserMessage) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for LLM generation")

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_message.text},
            ],
        )

        return response.choices[0].message.content or ""
