# BakeMate AGENT Guide

This file contains guidance for future contributors and automation agents working on the BakeMate repository.

## Repository Overview

- **Backend** – Python 3.12, FastAPI, SQLModel. Entry point is `backend/main.py`.
- **Frontend** – React + TypeScript via Vite, located in `frontend/`.
- **Docker** – `docker-compose.yml` orchestrates `backend`, `frontend` and an `nginx` reverse proxy.
- **Documentation** – Developer and user guides live under `docs/`.

## Development Environment

1. Install Python 3.12 and Node 20 if running outside Docker.
2. Python packages are listed in `backend/requirements.txt`.
3. Frontend dependencies are managed with npm (`package.json`).
4. `docker-compose up` starts the full stack for local development.

## Running Checks

The project uses pytest and black for backend code and ESLint for the frontend.

```bash
# Backend
cd backend
make test unit                       # run tests
make lint                            # lint

# Frontend
cd frontend && npm install
npm run lint                         # lint TypeScript/React files
```
Some tests rely on fixture data and may fail if certain files are missing. At minimum, ensure the test suite executes without import errors.

## Start Backend
```bash
cd backend
./scripts/startup.sh
```
If you run into startup error, ensure .venv dir exist and if not run: 'cd backend; make setup'

## Stop Backend
```bash
cd backend
./scripts/stop.sh
```

## Monitor Backend log file
```bash
cd backend
source .venv/bin/activate
python tools/log_watcher.py
```
To monitor the progress and errors for the backend, please use log_watcher.py

## Commit Guidelines

- Use short, descriptive commit messages (e.g. `Add inventory API` or `Fix order tests`).
- Keep changes focused; separate unrelated fixes into different commits.
- Update relevant documentation in `docs/` when behavior or interfaces change.
- Never commit secrets or credentials. Environment variables belong in a local `.env` file that is ignored by Git.

## Coding Style

- Follow PEP8 for Python code. The repository uses black in CI.
- Keep lines under 88 characters when practical.
- Use type hints for new Python functions.
- Frontend code should follow the existing ESLint rules (`npm run lint`).

## Useful References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)

Refer to `docs/developer_guide.md` for more detailed setup and deployment notes.
