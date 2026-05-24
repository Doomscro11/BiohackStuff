import pytest

from services import llm_provider
from services.llm_provider import generate_llm_text


@pytest.mark.asyncio
async def test_generate_llm_text_delegates_to_configured_boundary(monkeypatch):
    class FakeBoundary:
        async def generate_text(self, prompt: str) -> str:
            return f"boundary::{prompt}"

    monkeypatch.setattr(llm_provider, "get_llm_provider", lambda: FakeBoundary())

    assert await generate_llm_text("sample prompt") == "boundary::sample prompt"
