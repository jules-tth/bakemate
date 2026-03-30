# AGENTS: Repo Operating Guide for AI Assistants

This document defines how automation agents (e.g., Codex CLI) should work in this repository. It complements, but does not duplicate, AGENT.md (human contributor guide).

## Mission & Scope

- Focus: Implement targeted changes, keep edits minimal and aligned to existing style.
- Priority: Correctness, safety, and actionable guidance over verbosity.
- Constraint: Do not introduce unrelated refactors or features.

## Environment Assumptions

- Sandbox: workspace-write filesystem; network restricted unless escalated.
- Approvals: on-request for privileged actions (installs, network, destructive ops).
- Tools: prefer `rg` for search; edit files via `apply_patch` only.
- Read limits: read files in chunks ≤ 250 lines.
- Skip directories: ignore any `.venv/` folders when searching/reading.

## Repo Overview (for agents)

- Backend: FastAPI + SQLModel (Python), entry at `backend/main.py`; tests in `backend/tests`; virtualenv via `backend/Makefile`.
- Frontend: React + TypeScript (Vite) in `frontend/` with ESLint; Cypress E2E placeholders.
- Orchestration: `docker-compose.yml` with Nginx reverse proxy.
- Docs: `docs/developer_guide.md`, `docs/user_guide.md`.
- Human guide: `AGENT.md` (keep in sync when relevant behavior changes).

## Default Workflow

1. Plan: Use `update_plan` to outline concise steps; maintain exactly one `in_progress` item.
2. Explore: List files with `rg --files -g '!.venv/**'`; open only what’s needed with `sed -n` in ≤ 250-line chunks.
3. Implement: Use `apply_patch` to add/modify files; avoid broad rewrites.
4. Validate: If tests exist for touched areas, run backend tests via `cd backend && make test unit` when appropriate. Hold off if approvals are interactive unless necessary.
5. Summarize: Provide a clear, concise final message with what changed and next steps.

## When to Request Escalation

- Network access (e.g., `npm install`, pulling images, external fetches).
- Commands that write outside workspace or need privileged locations.
- Potentially destructive actions (e.g., `rm -rf`, `git reset`).

Prefer alternatives that do not require escalation. If escalation is necessary, justify briefly.

## Coding Guidelines (Agent-Specific)

- Minimal diffs: touch only files necessary for the task.
- Style: match local patterns (PEP8; black for Python; ESLint for frontend).
- Types: use type hints in Python where adding new functions.
- Tests: don’t add new test frameworks. Add targeted tests only if adjacent patterns show a clear place and it helps validate your change.
- Docs: update `README.md`, `AGENT.md`, or `docs/*` when behavior or interfaces change.
- No secrets: never add credentials. Respect `.env` being git-ignored.
- No license headers: do not add or change licensing unless asked.

## Backend Routines

- Setup venv: `cd backend && make setup`
- Run server: `cd backend && make run`
- Tests: `cd backend && make test unit` (pytest/coverage), `make lint` (black)
- For targeted pytest runs, prefer backend-local execution so imports resolve correctly: `cd backend && PYTHONPATH=. .venv/bin/pytest tests/unit/...`
- If `.venv` looks stale or miswired on this host, rebuild it with `cd backend && make setup` before claiming backend verification is blocked by code.
- Logs: `cd backend && python tools/log_watcher.py` (activate venv first)

## Frontend Routines

- Lint: `cd frontend && npm install && npm run lint`
- Dev server/build: follow `frontend/README.md` and Vite scripts; avoid installs unless necessary and approved.

## Message Style & Structure

- Preambles: Before tool calls, 1–2 short sentences on what’s next.
- Brevity: Keep responses concise; avoid heavy formatting unless helpful.
- Commands/paths: wrap in backticks. No ANSI codes.
- Final messages: summarize changes, rationale, and optional next steps (e.g., run tests, commit).

## Patching Rules

- Always use `apply_patch` with Add/Update/Delete headers.
- Do not re-read files redundantly after patching; rely on tool feedback.
- Avoid large multi-file changes in one patch unless tightly related.

## Safety & Non-Goals

- Do not commit or create branches unless explicitly requested.
- Do not change CI/CD, Docker, or Nginx configs unless the task requires.
- Do not perform destructive operations without explicit user direction.

## Cross-Referencing

- If you change agent behavior or expectations, update both this `AGENTS.md` and the human-facing `AGENT.md` with relevant notes to keep them aligned.

## Quick Checklist (per task)

- Understand scope; create/update a short plan.
- Search with `rg`; skip `.venv/`.
- Patch minimal code; follow local style.
- Update docs if interfaces/behavior change.
- Validate with focused tests when feasible.
- Summarize work and propose next steps.

