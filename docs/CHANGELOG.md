# Changelog

All notable changes to this project are documented here.

---

## v0.7.0 — Advanced SRE Capabilities (2026-07-29)

### Added
- **Rate Limiting:** Integrated `slowapi` to enforce a default `100/minute` global limit. 
  - *Tradeoff Note:* The default storage is in-memory. In a multi-replica deployment, the limit is applied per-pod (up to 200/min split across two pods).
  - *Probe Safety:* Health probes (`/healthz`, `/readyz`, `/metrics`, `/`) are strictly exempt from rate limits.
- **Upstream Retries:** Added `tenacity` backoff retries for transient upstream failures (Timeouts, ConnectErrors, and `502/503/504` statuses).
  - *Tradeoff Note:* Retries are strictly scoped to idempotent methods (`GET`, `HEAD`). `POST`, `PUT`, and `PATCH` are excluded to prevent duplicate actions on upstream systems.
- **Prometheus Metrics:** Added an unauthenticated `/metrics` endpoint tracking `gateway_requests_total` and `gateway_request_duration_seconds`. Metric path labels use resolved route templates to prevent cardinality explosions.
- **Pytest CI Suite:** Introduced an automated smoke suite in `.github/workflows/ci.yml` verifying auth, rate limits, and health probes before Docker builds.

## v0.6.0 — Security Minimums (2026-07-29)

### Added
- **Authentication:** Implemented opt-in Bearer token authentication for proxy routes via the `API_AUTH_TOKEN` environment variable (uses constant-time `secrets.compare_digest`). Health probes (`/healthz`, `/readyz`) deliberately bypass auth.
- **Security Context:** Kubernetes manifests now enforce `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true`, and `allowPrivilegeEscalation: false` with all capabilities dropped.
- **Non-Root Docker:** The Dockerfile now creates and runs as `gateway_user` (UID 1000) and mounts an `emptyDir` to `/tmp` for Uvicorn compatibility.
- **Dependency Pinning:** Pinned `fastapi`, `uvicorn`, `httpx`, and `pyyaml` to exact versions in `requirements.txt`. Base image pinned to `python:3.12.4-slim`.
- **Environment Template:** Added `.env.example` to document available environment variables.

### Changed
- **CORS Lockdown:** Removed `allow_credentials=True` and locked `allow_origins` to explicitly read from the `ALLOWED_ORIGINS` environment variable (defaulting to localhost).

## v0.5.0 — Core SRE Fundamentals (2026-07-29)

### Added
- **Health Probes:** Added explicit `/healthz` (liveness) and `/readyz` (readiness) endpoints, ensuring Kubernetes only routes traffic when routes are successfully loaded.
- **Structured Logging:** Replaced raw prints with standard `logging`, including a middleware that emits structured `key=value` lines with severity levels (`level=%(levelname)s`) and metadata (`request_id`, `duration_ms`, `method`, `path`, `status`).
- **Timeouts:** Implemented hardcoded timeouts for the global `httpx.AsyncClient` (`connect=5.0`, `read=30.0`, `write=30.0`, `pool=30.0`).
- **Graceful Shutdown:** Bound the `httpx.AsyncClient` lifecycle to a FastAPI `lifespan` context manager on `app.state.client`, ensuring clean connection closure on `SIGTERM`.

### Changed
- **Upstream Pass-Through:** Fixed a bug where upstream responses were always coerced via `.json()`. The proxy now returns the raw byte content, preserving non-JSON formats (e.g. HTML, CSV, 204s), and strips hop-by-hop headers to prevent compression conflicts.
- **Error Handling:** Gateway now catches specific `httpx` exceptions and maps them to semantic HTTP codes (`504 Gateway Timeout`, `502 Bad Gateway`, `500 Internal Server Error`) instead of a generic `502`, without leaking traceback details to the client.
- **Kubernetes Probes:** Updated `api-deployment.yaml` to point `livenessProbe` and `readinessProbe` to the new endpoints instead of the root `/`.

---

## v0.4.0 — CI/CD Pipeline (2026-07-27)

### Added
- **GitHub Actions CI:** Added an automated pipeline (`.github/workflows/ci.yml`) to verify Docker builds on every push.
- **Documentation:** Appended CI/CD pipeline details to `README.md`.

---

## v0.3.0 — SysOps Rebrand & NodePort Architecture

### Changed
- Rebranded project to "Universal API Gateway" for generic, plug-and-play orchestration.
- Upgraded Kubernetes `services.yaml` to use NodePort (`30000`) for direct external access (e.g. via n8n).

---

## v0.2.0 — Infrastructure

### Added
- **Kubernetes Manifests:** `k8s/` directory with `namespace.yaml`, `api-deployment.yaml`, and `services.yaml` for local cluster deployment.

### Changed
- Updated `README.md` with architecture diagram, repository structure, and project scope clarification.

---

## v0.1.0 — Core API & Containerization

### Added
- **FastAPI Application:** Entry point (`src/main.py`) with CORS middleware, health check endpoint, and versioned API prefix (`/api/v1`).
- **Dockerfile:** Single-stage `python:3.12-slim` container with dependency caching.
- **Documentation:** `api_documentation.md` (full API contract) and `walkthrough.md` (step-by-step guide).
