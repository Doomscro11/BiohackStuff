# LLM Provider Boundary

This document records the provider-boundary step introduced by Unbuildr.

## Purpose

BiohackStuff currently uses an Emergent-backed LLM integration for peptide analogue generation. The completion path is to move provider-specific imports and request handling behind a narrow adapter interface so future providers, test doubles, and production guardrails can be added without spreading provider logic through application code.

## Added Boundary

The adapter module is:

```text
backend/services/llm_provider.py
```

It defines:

```text
LLMProvider protocol
EmergentLLMProvider implementation
get_llm_provider()
generate_llm_text(prompt)
```

## Safety Posture

This step preserves the existing Emergent-backed behavior. It does not add a new provider, new credentials, production access, auto-selection, or deployment behavior.

## Next Wiring Step

The next guarded PR should update `backend/server.py` to:

1. Remove direct imports from `emergentintegrations.llm.chat`.
2. Import `generate_llm_text` from `services.llm_provider`.
3. Replace the direct `get_llm_chat()` / `UserMessage` call with `await generate_llm_text(prompt)`.
4. Keep runtime output and parser behavior unchanged.

## Non-Goals

This PR does not:

- change LLM model selection
- introduce OpenAI/Gemini direct SDK usage
- change prompt content
- change parsing logic
- change billing/credit behavior
- change production configuration
