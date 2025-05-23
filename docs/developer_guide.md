---

# BakeMate Developer Guide

## 1. Introduction

Welcome to the BakeMate Developer Guide! This document provides instructions on how to set up your development environment, understand the project structure, run tests, and deploy the BakeMate application.

BakeMate is a web-first SaaS application designed for solo U.S. bakers. Its architecture consists of:
- **Frontend:** A React application built with Vite and styled using Tailwind CSS. It is served as static files by Nginx in production.
- **Backend:** A Python-based API built with FastAPI, using SQLModel for ORM and Pydantic for data validation. It supports SQLite for local development and is designed with an adapter pattern that could support other databases like Airtable (conceptualized) for production.
- **Deployment:** The application is containerized using Docker and orchestrated with Docker Compose for local development and can be adapted for production deployments.
- **Proxy:** Nginx is used as a reverse proxy to route requests to the frontend and backend services.

## 2. Prerequisites

Before you begin, ensure you have the following software installed on your system:
- **Git:** For version control.
- **Docker and Docker Compose:** For containerization and running the application services.
- **Node.js and npm (or yarn/pnpm):** Required for frontend development if working directly on the frontend outside of Docker, and for running frontend build/test scripts. (Node.js v18+ recommended)
- **Python:** (v3.11+ recommended) and pip: Required for backend development if working directly on the backend outside of Docker.
- **A Code Editor:** Such as Visual Studio Code, Sublime Text, or PyCharm.

## 3. Getting the Code

First, clone the repository to your local machine (assuming the project will be hosted on a Git platform):

```bash
# git clone <repository_url>
# cd bakemate
```
For the current environment, the code is located at `/home/ubuntu/bakemate`.

## 4. Project Structure Overview

The project is organized as a monorepo with distinct frontend and backend directories:

```
/bakemate
├── .env.example        # Example environment variables
├── .github/
│   └── workflows/
│       └── ci.yml      # GitHub Actions CI configuration
├── backend/
│   ├── app/            # Core FastAPI application logic
│   │   ├── api/        # API endpoint routers
│   │   ├── auth/       # Authentication logic
│   │   ├── core/       # Configuration, settings
│   │   ├── models/     # SQLModel data models
│   │   ├── repositories/ # Data Access Layer (DAL) adapters
│   │   └── services/   # Business logic services
│   ├── tests/          # Backend tests (e.g., Playwright API tests)
│   ├── Dockerfile      # Instructions to build the backend Docker image
│   ├── main.py         # FastAPI application entry point
│   └── requirements.txt # Python dependencies
├── docs/
│   ├── developer_guide.md # This guide
│   └── user_guide.md    # Application user manual
├── frontend/
│   ├── cypress/        # Cypress E2E tests
│   ├── public/         # Static assets for Vite
│   ├── src/            # Frontend React/TypeScript source code
│   ├── Dockerfile      # Instructions to build the frontend Docker image (serves static files with Nginx)
│   ├── index.html      # Main HTML entry point for Vite
│   ├── package.json    # Node.js dependencies and scripts
│   ├── postcss.config.js # PostCSS configuration
│   ├── tailwind.config.js # Tailwind CSS configuration
│   └── vite.config.ts  # Vite configuration
├── docker-compose.yml  # Docker Compose configuration for services
├── nginx.conf          # Nginx reverse proxy configuration
└── README.md           # Project overview and setup instructions
```

## 5. Setting Up a Development Environment (Using Docker Compose)

This is the recommended method for local development as it mirrors the production setup closely.

### 5.1. Environment Variables

1.  Create a `.env` file in the project root directory (`/home/ubuntu/bakemate/.env`) by copying from `.env.example` (if provided) or creating it manually.
2.  Populate the `.env` file with necessary environment variables. Refer to `docker-compose.yml` and `backend/app/core/config.py` for required variables. Key variables include:

    ```env
    # Backend Configuration
    DATABASE_URL="sqlite:///./bakemate_dev.db" # For local SQLite
    SECRET_KEY="your_super_secret_random_key_here" # Generate a strong random key
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    SERVER_HOST="http://localhost" # Or your domain if deploying

    # Email Configuration (Optional, for email features)
    SENDGRID_API_KEY="YOUR_SENDGRID_API_KEY"
    EMAILS_FROM_EMAIL="your_verified_sender@example.com"
    # For testing, you can use MailHog or similar, or leave blank if email features are not critical for current dev task.

    # Airtable Configuration (Optional, if using Airtable adapter for production-like testing)
    # AIRTABLE_API_KEY="YOUR_AIRTABLE_API_KEY"
    # AIRTABLE_BASE_ID="YOUR_AIRTABLE_BASE_ID"
    # DB_ADAPTER="sqlite" # or "airtable" to switch DAL

    # Docker Compose specific (usually not needed in .env if defaults in compose are fine)
    # POSTGRES_USER=user
    # POSTGRES_PASSWORD=password
    # POSTGRES_DB=bakemate
    ```

### 5.2. Build and Run Docker Containers

From the project root directory (`/home/ubuntu/bakemate`):

```bash
docker-compose up --build -d
```

This command will:
- Build the Docker images for the `backend`, `frontend`, and `nginx` services if they don't exist or if their Dockerfiles have changed.
- Start all services in detached mode (`-d`).

### 5.3. Accessing the Application

-   **Frontend Application:** `http://localhost` (or the port mapped to Nginx, typically 80 or 8080 as per `docker-compose.yml`).
-   **Backend API:** Requests to `http://localhost/api/v1/` will be proxied by Nginx to the backend service.
-   **Backend API Docs (Swagger UI):** `http://localhost:8000/docs` (accessing the backend service directly on its exposed port).

### 5.4. Making Code Changes

-   **Backend:** The backend service uses Uvicorn with `--reload`, so changes made to Python files in `/home/ubuntu/bakemate/backend/app` should automatically trigger a server reload within the container.
-   **Frontend:** The current `frontend/Dockerfile` creates a production build of the static assets and serves them with Nginx. For live-reloading during frontend development:
    1.  You can modify the `frontend` service in `docker-compose.yml` to run the Vite dev server (`npm run dev`) instead of Nginx.
    2.  Ensure `vite.config.ts` is configured for HMR over Docker (e.g., `server: { host: true, port: 5173, strictPort: true, watch: { usePolling: true } }`).
    3.  Mount the `/frontend/src` directory as a volume.
    4.  Expose the Vite dev server port (e.g., 5173) and update the Nginx proxy to point to it for frontend requests, or access it directly.
    Alternatively, run the frontend dev server manually on your host machine (see section 6.2).

### 5.5. Viewing Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### 5.6. Stopping the Environment

```bash
docker-compose down
```
To remove volumes (like the database): `docker-compose down -v`

## 6. Setting Up a Development Environment (Without Docker - Manual)

This method is for developers who prefer to run services directly on their host machine.

### 6.1. Backend (FastAPI)

1.  Navigate to the backend directory: `cd /home/ubuntu/bakemate/backend`
2.  Create and activate a Python virtual environment:
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```
3.  Install dependencies: `pip install -r requirements.txt`
4.  Set required environment variables directly in your shell or using a `.env` file loaded by your application (e.g., using `python-dotenv` if you add it to `main.py`).
5.  Run the development server:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The backend API will be available at `http://localhost:8000`.

### 6.2. Frontend (React/Vite)

1.  Navigate to the frontend directory: `cd /home/ubuntu/bakemate/frontend`
2.  Install Node.js dependencies: `npm install` (or `yarn install` / `pnpm install`)
3.  Run the Vite development server:
    ```bash
    npm run dev
    ```
    The frontend will typically be available at `http://localhost:5173` (check console output for the exact URL).
4.  **API Configuration:** Ensure your frontend code makes API requests to `http://localhost:8000/api/v1/` (the backend server URL). This might involve setting an environment variable like `VITE_API_BASE_URL` in a `.env` file in the `/frontend` directory and using it in your API client.

## 7. Running Tests

### 7.1. Backend API Tests (Playwright)

Placeholder API tests are located in `/home/ubuntu/bakemate/backend/tests/api/`. These tests are written using Playwright.

1.  Ensure the backend server is running (either via Docker or manually).
2.  Navigate to the project root or backend directory.
3.  You might need to install Playwright and its browser drivers if not already done: `npm install -D @playwright/test && npx playwright install` (typically managed via a `package.json` in the `backend/tests` or root directory for test dependencies).
4.  Run the tests:
    ```bash
    # From the directory where Playwright config is (or specify path to config/tests)
    # npx playwright test
    ```
    (The current setup has a `.spec.ts` file, implying a TypeScript test setup which might require `ts-node` or pre-compilation if not handled by Playwright's runner directly.)
    For the provided structure, you would typically run Playwright tests from a context where Node.js and Playwright are installed. The `api_playwright_spec.spec.ts` is a placeholder and would need actual test logic and potentially a `playwright.config.ts`.

### 7.2. Frontend E2E Tests (Cypress)

Placeholder E2E tests are located in `/home/ubuntu/bakemate/frontend/cypress/integration/`.

1.  Ensure the frontend development server (or a built version) and the backend server are running and accessible.
2.  Navigate to the frontend directory: `cd /home/ubuntu/bakemate/frontend`
3.  Install Cypress if it's the first time: `npm install cypress --save-dev`
4.  Open the Cypress Test Runner:
    ```bash
    npx cypress open
    ```
5.  Or run tests headlessly:
    ```bash
    npx cypress run
    ```
    Update `cypress.json` or `cypress.config.js` with `baseUrl` (e.g., `http://localhost:5173` or `http://localhost` if using Docker setup).

## 8. Deployment to Production

### 8.1. General Principles

-   **Environment Variables:** All secrets (API keys, database credentials, `SECRET_KEY`) MUST be managed securely (e.g., using environment variables injected by the hosting platform, HashiCorp Vault, AWS Secrets Manager, etc.). Do not commit secrets to Git.
-   **Database:** For production, use a robust, managed database service. The current SQLite setup is for development. The Airtable adapter is a conceptual example of using a cloud-based datastore.
-   **HTTPS:** Production deployments must use HTTPS. This is typically handled by a load balancer or reverse proxy in front of your application (e.g., Nginx, Caddy, or managed services on cloud platforms).
-   **Logging & Monitoring:** Implement comprehensive logging and monitoring.

### 8.2. Using Docker Compose (for a single server or simpler deployments)

1.  **Production `.env` file:** Create a `.env` file on the server with production-specific values. Ensure `DATABASE_URL` points to your production database and all API keys are production keys.
2.  **Build Images (or Pull from Registry):**
    -   If building on the server: `docker-compose build`
    -   If pulling pre-built images from a Docker registry (recommended): Ensure your `docker-compose.yml` (or a `docker-compose.prod.yml`) references these images.
3.  **Run Application:**
    ```bash
    docker-compose up -d
    ```
4.  **Nginx as Edge Proxy:** The provided `nginx.conf` and `docker-compose.yml` set up Nginx to proxy requests. If this Nginx instance is your edge server, configure it for HTTPS (e.g., using Let's Encrypt with Certbot).

### 8.3. Deploying Frontend and Backend Separately

-   **Frontend (Static Build):**
    1.  Build the frontend: `cd /home/ubuntu/bakemate/frontend && npm run build`. This creates static assets in `/home/ubuntu/bakemate/frontend/dist`.
    2.  Deploy the `dist` folder to a static hosting service (e.g., Netlify, Vercel, AWS S3 + CloudFront, GitHub Pages). The URL `https://tsopphqt.manus.space` is an example of such a deployment.
    3.  Configure the frontend build to use the production backend API URL (e.g., via `VITE_API_BASE_URL` environment variable during the build process).
-   **Backend (Docker Image):**
    1.  Build the backend Docker image: `cd /home/ubuntu/bakemate/backend && docker build -t bakemate-backend .` (or use `docker-compose build backend`).
    2.  Push the image to a container registry (e.g., Docker Hub, AWS ECR, Google GCR).
    3.  Deploy the image to a container hosting service (e.g., Fly.io, Render.com, AWS ECS, Google Cloud Run, Kubernetes).
    4.  Configure all necessary environment variables on the hosting platform.
    5.  **CORS:** Ensure the backend FastAPI application has CORS (Cross-Origin Resource Sharing) configured to allow requests from your frontend's production domain.

## 9. CI/CD Pipeline

The project includes a basic CI pipeline defined in `.github/workflows/ci.yml`. This pipeline currently:
-   Lints and tests the backend code.
-   Lints and tests the frontend code.
-   Builds Docker images for the backend and frontend.

For a full CI/CD setup, this pipeline can be extended to:
-   Push built Docker images to a container registry upon merges to the `main` branch or on new tags.
-   Trigger automated deployments to staging and production environments based on branch strategies or tags.

## 10. Important Files for Deployment Confirmation

To confirm the application is ready for deployment (especially using the Dockerized approach), ensure these files are correctly configured and present:

-   **`docker-compose.yml`:** Defines all services, their builds, ports, volumes, and environment variable sources.
-   **`nginx.conf`:** Correctly configures Nginx as a reverse proxy for the frontend and backend services.
-   **`backend/Dockerfile`:** Successfully builds a runnable production image for the FastAPI backend.
-   **`backend/requirements.txt`:** Contains all necessary Python dependencies for the backend.
-   **`frontend/Dockerfile`:** Successfully builds the frontend static assets and sets up Nginx to serve them.
-   **`frontend/package.json`:** Contains all necessary Node.js dependencies for building the frontend and running scripts.
-   **`.env` file (on the server, not in Git):** Contains all required environment variables with production-appropriate values.
-   All application source code in `/backend/app/` and `/frontend/src/`.

This guide should provide a solid starting point for developing, testing, and deploying the BakeMate application. Happy developing!

---

