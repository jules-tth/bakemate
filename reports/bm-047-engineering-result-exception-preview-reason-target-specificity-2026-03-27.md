# BM-047 Engineering Result: Exception Preview Reason Target Specificity

## Source Reviewed

- `backend/app/services/order_service.py`
- `backend/tests/unit/test_orders_bm033_day_running_focus.py`

## Files Changed

- `backend/app/services/order_service.py`
- `backend/tests/unit/test_orders_bm033_day_running_focus.py`

## What Landed

- Tightened the compact queue reason fallback wording in `OrderService._build_queue_reason_preview(...)` for the remaining generic queue-only cases:
  - `production basics missing` -> `Bake details missing`
  - `production details need clarification` -> `Bake details need clarification`
  - `contact basics missing` -> `Contact details missing`
  - `handoff basics missing` -> `Handoff details missing`
- Kept the blocker/attention prefix behavior unchanged.
- Kept `Next: ...` wording unchanged.
- Kept the existing two-line exception preview pattern unchanged.
- Kept scope limited to queue reason wording only.
- Added a focused BM-047 helper test that locks the updated generic fallback wording.

## Verification Commands And Results

- `cd /Users/jules/.openclaw/workspace/bakemate/backend && ./.venv/bin/pytest tests/unit/test_orders_bm033_day_running_focus.py --cov=app.services.order_service --cov-report=term-missing`
  - Result: test assertions passed, but command exited nonzero because repo-wide coverage fail-under `80` is not reachable from this targeted slice run alone (`66%` for `app/services/order_service.py`).
- `cd /Users/jules/.openclaw/workspace/bakemate/backend && PYTHONPATH=. ./.venv/bin/pytest tests/unit/test_orders_bm033_day_running_focus.py --cov=app.services.order_service --cov-report=term-missing --cov-fail-under=0`
  - Result: passed, `17 passed`, targeted coverage report emitted, `66%` for `app/services/order_service.py`.
- `cd /Users/jules/.openclaw/workspace/bakemate/frontend && npm run build`
  - Result: passed, production build completed successfully.

## Caveats

- The originally requested artifact directory `/Users/jules/.openclaw/workspace/projects/bakemate/reports/` is not writable in this sandboxed session, so this report was written to the repo-local fallback path `/Users/jules/.openclaw/workspace/bakemate/reports/`.
- The focused pytest run emits existing `ResourceWarning` messages about unclosed SQLite connections in the test process; this slice did not change that behavior.
