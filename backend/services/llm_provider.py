"""LLM provider adapter boundary for peptide analogue generation.

This module intentionally preserves the existing Emergent-backed behavior while
moving provider-specific imports and request handling out of the FastAPI entrypoint.

Future providers should be added behind this boundary instead of being imported
directly in route or business-logic modules.
"""

import os
import uuid
from dataclasses import dataclass
from typing import Protocol

from emergentintegrations.llm.chat import LlmChat, UserMessage


PEPTIMANCER_SYSTEM_MESSAGE = """You are Peptimancer, an expert AI peptide architect specializing in generating novel peptide analogues.

Your expertise includes:
- Advanced peptide chemistry (substitutions, D-isomers, lipidation, cyclization)
- Structure-activity relationships (SAR)
- Pharmacokinetic optimization
- Intellectual property considerations
- Biological plausibility assessment

For each analogue, provide:
1. A unique descriptive name
2. Modified sequence with clear notation
3. 1-3 specific modifications applied
4. Precise modification positions
5. IP risk assessment (0-10 scale)
6. Novelty score (0-10 scale)
7. Affinity estimate (qualitative)
8. PK estimate (qualitative)

Focus on creating patent-differentiated analogues that preserve or enhance biological function."""


class LLMProvider(Protocol):
    async def generate_text(self, prompt: str) -> str:
        """Generate text for a prompt."""


@dataclass
class EmergentLLMProvider:
    """Emergent-backed provider preserving the current runtime behavior."""

    api_key: str | None = None
    model_provider: str = "openai"
    model_name: str = "gpt-4"
    system_message: str = PEPTIMANCER_SYSTEM_MESSAGE

    async def generate_text(self, prompt: str) -> str:
        chat = LlmChat(
            api_key=self.api_key or os.environ.get("EMERGENT_LLM_KEY"),
            session_id=str(uuid.uuid4()),
            system_message=self.system_message,
        ).with_model(self.model_provider, self.model_name)
        return await chat.send_message(UserMessage(text=prompt))


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider.

    The default remains Emergent to avoid behavior changes in this PR. Provider
    selection can be expanded in a later guarded PR.
    """

    return EmergentLLMProvider()


async def generate_llm_text(prompt: str) -> str:
    """Generate text through the configured provider boundary."""

    provider = get_llm_provider()
    return await provider.generate_text(prompt)
