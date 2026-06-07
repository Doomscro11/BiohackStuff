"""Tests for the BiohackStuff LLM provider boundary.

The application must not import or depend on Emergent LLM packages. Route and
business logic should call the local provider boundary instead of vendor SDKs.
"""

import importlib

import pytest

from services import llm_provider


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic():
    provider = llm_provider.MockLLMProvider()

    first = await provider.generate_text("generate peptide analogue")
    second = await provider.generate_text("generate peptide analogue")

    assert first == second
    assert "Mock GLP-1 Analogue Alpha" in first
    assert "### Analogue:" in first


def test_ci_mode_uses_mock_provider(monkeypatch):
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    provider = llm_provider.get_llm_provider()

    assert isinstance(provider, llm_provider.MockLLMProvider)


def test_demo_mode_uses_mock_provider(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    provider = llm_provider.get_llm_provider()

    assert isinstance(provider, llm_provider.MockLLMProvider)


def test_explicit_mock_mode_uses_mock_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("DEMO_MODE", raising=False)

    provider = llm_provider.get_llm_provider()

    assert isinstance(provider, llm_provider.MockLLMProvider)


def test_live_provider_requires_explicit_openai_key(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    provider = llm_provider.get_llm_provider()

    assert isinstance(provider, llm_provider.OpenAICompatibleProvider)


@pytest.mark.asyncio
async def test_live_provider_fails_closed_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = llm_provider.OpenAICompatibleProvider(api_key=None)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is required"):
        await provider.generate_text("prompt")


def test_emergent_package_is_not_importable():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("emergentintegrations.llm.chat")
