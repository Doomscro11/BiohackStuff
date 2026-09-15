# Target Project State: Doomscro11/BiohackStuff

Generated: 2026-09-14T18:50:00Z
Target branch: `main`
Operator mode: `audit` (manual re-audit)
Read-only: `True`
Mutation allowed: `False`

## Detected stack
- CRACO
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
Score: **98/100**
Confidence: `high`

## Blockers (all resolved)
1. ~~missing_project_state~~ — ✅ Resolved via PRs #22, #23. `docs/PROJECT_STATE.md` exists and is reviewed.
2. ~~emergent_dependency_present~~ — ✅ Resolved. Provider adapter boundary at `backend/services/llm_provider.py`. Tests pass (7/7 in `test_llm_provider_boundary.py`). No Emergent SDK imports.
3. ~~demo_otp_guard_needed~~ — ✅ Resolved via PR #29. `backend/startup_guards.py` with `check_demo_otp_in_production()`. Tests pass (4/4 in `test_startup_guards.py`).
4. ~~manual_ops_commands_present~~ — ✅ Resolved via PRs #25, #26 + docs. `Makefile` deploys `require-manual-ops` guard. Deployment/backup/restore/rollback gated behind `CONFIRM_MANUAL_OPS=yes`.

## Remaining polish (non-blocking)
- Full backend test suite requires local MongoDB (38+ tests pass)
- Frontend build requires `.env` with `REACT_APP_API_URL` (CI validates it)
- README could mention seed-data flow
- `docs/generated/unbuildr/` should be gitignored or versioned

## Fail-closed rule
BiohackStuff remains read-only for automated mutations. All changes gated through PRs with CI validation.