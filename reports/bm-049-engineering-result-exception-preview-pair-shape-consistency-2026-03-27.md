# BM-049 Engineering Result — Exception Preview Pair-Shape Consistency

Date: 2026-03-27
Engineer: Codex
Milestone: BM-049
Status: complete

## Artifact location note
The requested artifact path under `/Users/jules/.openclaw/workspace/projects/bakemate/reports/` is outside the writable workspace for this run. This result was written to the repo-local fallback:

- `/Users/jules/.openclaw/workspace/bakemate/reports/bm-049-engineering-result-exception-preview-pair-shape-consistency-2026-03-27.md`

## Scope handled
- Kept the change queue-only and helper-only.
- Preserved blocker/attention selection logic.
- Preserved `next_step` selection logic and meaning.
- Preserved severity cueing, queue ordering, counts, grouping, filtering, action classes, routing, and detail behavior.
- Preserved the two-line `Blocked:` / `Attention:` then `Next:` pattern.
- Preserved BM-048 bake-target alignment.

## Changes made
- Updated the compact queue next-step helper so saved-contact follow-up now stays in the `contact details` noun family: `Next: use contact details`.
- Updated the compact queue reason helper so the backup-contact fallback now uses `Backup contact details missing`.
- Updated the compact queue reason helper so the pickup-vs-delivery blocker now reads `Handoff method not confirmed`, keeping the issue specific while matching the handoff target family better.
- Updated focused BM-033 unit expectations to cover the revised contact and handoff pair shapes.

## Verification
- Backend targeted coverage run:
  - Command: `cd /Users/jules/.openclaw/workspace/bakemate/backend && PYTHONPATH=. .venv/bin/pytest tests/unit/test_orders_bm033_day_running_focus.py --cov=app.services.order_service --cov-report=term --cov-fail-under=0 -q`
  - Result: `18 passed in 0.37s`
  - Coverage for `app/services/order_service.py`: `66%`
  - Note: the same targeted command without `--cov-fail-under=0` failed only because the repo enforces a global `80%` fail-under against a single-file test slice.
- Frontend build:
  - Command: `cd /Users/jules/.openclaw/workspace/bakemate/frontend && npm run build`
  - Result: success, Vite production build completed in `639ms`
  - Note: build emitted a non-blocking Browserslist staleness warning about `caniuse-lite`.

## Files changed
- `/Users/jules/.openclaw/workspace/bakemate/backend/app/services/order_service.py`
- `/Users/jules/.openclaw/workspace/bakemate/backend/tests/unit/test_orders_bm033_day_running_focus.py`
- `/Users/jules/.openclaw/workspace/bakemate/reports/bm-049-engineering-result-exception-preview-pair-shape-consistency-2026-03-27.md`
