# BakeMate

BakeMate is an open source, web-first SaaS platform that helps solo U.S. bakers manage every part of their business. It is built with a **FastAPI** backend and a **React + TypeScript** frontend served via **Nginx**. Docker Compose orchestrates the stack for local development.

## Features

- Ingredient and recipe management
- Pricing and order tracking with Stripe integration
- Calendar and task management
- Expense and mileage tracking
- Reports and analytics
- Differentiators such as an embeddable mini-shop, real-time inventory tracking and email marketing hooks

## Getting Started

BakeMate should be run in **Docker Compose by default** for development. Do not rely on ad-hoc host-run frontend/backend processes as the normal workflow.

Before changing any BakeMate host port mappings, first read `/home/jules/.openclaw/workspace/PORTS.md` and run `/home/jules/.openclaw/workspace/scripts/check-port.sh <port>`.

```bash
docker compose up --build -d
```

This starts:
- backend on host port `8300`
- frontend container on host port `3300`
- Nginx reverse proxy on host port `8301`

Recommended access points:
- app via reverse proxy: `http://localhost:8301/`
- app via LAN: `http://<your-lan-ip>:8301/`
- backend health: `http://localhost:8300/health`

For this host specifically, the current LAN URL is:
- `http://192.168.86.24:8301/`

Keep the Docker dev environment running while implementation work is in progress unless a task explicitly requires rebuilding/restarting it.

For a detailed setup guide, see [docs/developer_guide.md](docs/developer_guide.md). User-facing instructions live in [docs/user_guide.md](docs/user_guide.md).

### Running Checks

Backend linting and tests:

```bash
cd backend
make lint
make test unit
```

Frontend linting:

```bash
cd frontend
npm install
npm run lint
```

## Contributing

Contributions are always welcome! Feel free to open issues or submit pull requests if you find bugs or have ideas for improvements.

## License

License information will be added soon.
