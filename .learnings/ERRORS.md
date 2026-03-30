# Errors

## [ERR-20260319-001] exec-rg-missing

**Logged**: 2026-03-19T12:32:00-04:00
**Priority**: low
**Status**: pending
**Area**: infra

### Summary
`rg` is not installed in this environment, so repo search should use `grep`/`find` instead.

### Error
```
/bin/bash: line 1: rg: command not found
```

### Context
- Command attempted: `rg -n "day_running|Day-running triage|readiness_label|day_running_focus_summary|queue counts|imported_counts|counts" backend frontend tests -S`
- Workdir: `/home/jules/.openclaw/workspace/bakemate`

### Suggested Fix
Use `grep -RIn` for code search in this environment.

### Metadata
- Reproducible: yes
- Related Files: .learnings/ERRORS.md

---
## [ERR-20260319-002] pytest-missing-pythonpath

**Logged**: 2026-03-19T12:40:00-04:00
**Priority**: low
**Status**: pending
**Area**: tests

### Summary
Backend pytest commands in this repo require `PYTHONPATH=.` when run from `backend/`.

### Error
```
ModuleNotFoundError: No module named 'app'
```

### Context
- Command attempted without `PYTHONPATH=. ` prefix from `backend/`
- Tests import modules via `app.*`

### Suggested Fix
Run backend tests as `PYTHONPATH=. ../backend/.venv/bin/pytest ...` from `backend/`.

### Metadata
- Reproducible: yes
- Related Files: .learnings/ERRORS.md

---
