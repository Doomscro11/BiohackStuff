# Target Project State: Doomscro11/BiohackStuff

Generated: 2026-05-31T14:13:04.177480+00:00
Target branch: `main`
Operator mode: `audit`
Read-only: `True`
Mutation allowed: `False`

## Detected stack
- CRACO
- Emergent LLM integration
- FastAPI
- Jest
- MongoDB/Motor
- Playwright
- Python requirements
- React
- Yarn
- pytest

## Entrypoints
- `backend/server.py`
- `frontend/src/App.js`
- `frontend/src/MainApp.js`
- `frontend/src/index.js`
- `Makefile`

## Completion score
Score: **82/100**
Confidence: `high`

## Ranked blockers
1. **missing_project_state** — `high`
   - Recommended action: Generate reviewed target_project_state.md before mutation.
2. **emergent_dependency_present** — `high`
   - Recommended action: Replace Emergent integration with a reviewed provider adapter.
3. **demo_otp_guard_needed** — `medium`
   - Recommended action: Fail closed for demo OTP in production.
4. **manual_ops_commands_present** — `medium`
   - Recommended action: Mark deployment, rollback, backup, and restore commands manual-only.

## Fail-closed rule
BiohackStuff and other external targets remain read-only until the audit plan is reviewed.
