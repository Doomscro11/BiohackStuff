"""Temporary compatibility shim for legacy LLM imports.

New code should import from `services.llm_service` directly. This shim exists
only to keep older call sites working during the monorepo stabilization pass.
"""

from services.llm_service import LlmChat, UserMessage

__all__ = ["LlmChat", "UserMessage"]
