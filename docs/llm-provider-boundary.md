# LLM Provider Boundary

This document records the provider-boundary state introduced and finalized by Unbuildr.

## Purpose

BiohackStuff must not depend on Emergent LLM packages or direct Emergent imports. Provider-specific SDK usage belongs behind a narrow local adapter so route and business logic can call one stable interface while tests, CI, demo mode, and live mode remain explicit.

## Boundary Module

The adapter module is:

```text
backend/services/llm_provider.py
```

It defines:

```text
LLMProvider protocol
MockLLMProvider implementation
OpenAICompatibleProvider implementation
get_llm_provider()
generate_llm_text(prompt)
```

## Runtime Selection

Provider selection is explicit:

- `LLM_PROVIDER=mock` uses the deterministic local mock provider.
- `CI=true` uses the deterministic local mock provider.
- `DEMO_MODE=true` uses the deterministic local mock provider.
- Live mode uses the OpenAI-compatible provider and requires `OPENAI_API_KEY`.

The live provider fails closed when no explicit API key is configured.

## Safety Posture

This boundary keeps provider SDK calls out of route and domain logic. It does not introduce auto-provider selection, production deployment behavior, secret handling, or auto-merge behavior.

The repository release gate also verifies that the external `emergentintegrations` package is not installed.

## Completed Wiring

`backend/server.py` imports:

```text
services.llm_provider.generate_llm_text
```

Peptide analogue generation calls:

```text
await generate_llm_text(prompt)
```

No direct `emergentintegrations.llm.chat` route import is required.

## Guard Tests

The boundary is guarded by:

```text
backend/tests/test_llm_provider_boundary.py
```

The tests verify:

- mock provider determinism
- CI mode uses mock provider
- demo mode uses mock provider
- explicit mock mode uses mock provider
- live provider requires explicit OpenAI configuration
- live provider fails closed without a key
- Emergent chat package import is unavailable

## Non-Goals

This step does not:

- change prompt content
- change parsing logic
- change billing or credit behavior
- add production credentials
- add deployment automation
- add production access
