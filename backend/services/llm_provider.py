"""LLM provider adapter boundary for peptide analogue generation.

Provider-specific SDK usage belongs in this module, not in route or business
logic modules. The project standard is that BiohackStuff must not depend on
Emergent packages or imports.
"""

import os
from dataclasses import dataclass
from typing import Protocol

from openai import AsyncOpenAI


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
class OpenAICompatibleProvider:
    """OpenAI-compatible provider with explicit environment configuration."""

    api_key: str | None = None
    model_name: str | None = None
    system_message: str = PEPTIMANCER_SYSTEM_MESSAGE

    async def generate_text(self, prompt: str) -> str:
        resolved_api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for live text generation")

        client = AsyncOpenAI(api_key=resolved_api_key)
        response = await client.chat.completions.create(
            model=self.model_name or os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("LLM provider returned an empty response")
        return content


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider.

    BiohackStuff does not use Emergent dependencies. The default provider is an
    OpenAI-compatible SDK boundary using explicit environment configuration.
    """

    return OpenAICompatibleProvider()


async def generate_llm_text(prompt: str) -> str:
    """Generate text through the configured provider boundary."""

    provider = get_llm_provider()
    return await provider.generate_text(prompt)
