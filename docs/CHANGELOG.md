# Changelog

All notable changes to this project are documented here.

---

## v0.4.0 — CI/CD Pipeline (2026-07-27)

### Added
- **GitHub Actions CI:** Added an automated pipeline (`.github/workflows/ci.yml`) to verify Docker builds on every push.
- **Documentation:** Appended CI/CD pipeline details to `README.md`.

---

## v0.3.0 — SysOps Rebrand & NodePort Architecture

### Changed
- Removed the Admin UI entirely to focus strictly on DevOps infrastructure.
- Rebranded project to "Universal API Gateway" for generic, plug-and-play orchestration.
- Upgraded Kubernetes `services.yaml` to use NodePort (`30000`) for direct external access (e.g. via n8n).

---

## v0.2.0 — Infrastructure

### Added
- **Kubernetes Manifests:** `k8s/` directory with `namespace.yaml`, `api-deployment.yaml`, and `services.yaml` for local cluster deployment.
- **Auth Route:** `/api/v1/auth` endpoint for basic authentication flow.

### Changed
- Updated `README.md` with architecture diagram, repository structure, and project scope clarification.

---

## v0.1.0 — Core API & Containerization

### Added
- **FastAPI Application:** Entry point (`src/main.py`) with CORS middleware, health check endpoint, and versioned API prefix (`/api/v1`).
- **Stock Routes:** Real-time stock pricing and OHLCV history via Yahoo Finance (`src/api/routes/stocks.py`).
- **Watchlist Routes:** CRUD endpoints for user watchlists (`src/api/routes/watchlist.py`).
- **Alert Routes:** Pattern-based trading alert management (`src/api/routes/alerts.py`).
- **Data Models:** Pydantic validation for alert payloads (`src/api/models/alerts.py`).
- **Dockerfile:** Single-stage `python:3.12-slim` container with dependency caching.
- **Documentation:** `api_documentation.md` (full API contract) and `walkthrough.md` (step-by-step guide).
