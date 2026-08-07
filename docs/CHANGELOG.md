# Changelog

All notable changes to this project are documented here.

---

## v0.8.0 — CI/CD Hardening (2026-08-07)

### Added
- **Six-gate CI pipeline:** `.github/workflows/ci.yml` now runs lint, tests, dependency audit, infrastructure validation, secret scanning, and image scanning in parallel. All six must pass before the image is published to GHCR. Previously only `pytest` and a Docker dry-run build gated the publish, leaving the Terraform and Kubernetes layers — a large share of the repository — entirely unvalidated.
- **Infrastructure validation:** `terraform fmt -check` plus `terraform validate` for `terraform/aks` (using `init -backend=false`, so no state or cloud credentials are needed), `kustomize build` for the base and the cloud overlay, and `kubeconform -strict` against real Kubernetes API schemas.
  - *Limitation:* `terraform validate` does not contact the compute API, so it passes against configurations that cannot apply — see the AKS VM-size failure in [Troubleshooting](TROUBLESHOOTING.md). A green job means "this parses", not "this deploys".
- **Image scanning:** Trivy fails the build on any HIGH/CRITICAL CVE that has a fix available. Runs with `--ignore-unfixed` so unpatchable distro CVEs cannot make the pipeline permanently unfixable; a second non-blocking step reports the full picture including MEDIUM and unfixed.
- **Secret scanning:** `gitleaks` across the full commit history (`fetch-depth: 0` — the default shallow clone would let the gate pass without scanning anything).
- **Dependency audit:** `pip-audit` over both requirements files. Dev dependencies are included deliberately: they run with access to the repository and CI secrets even though they never ship in the image.
- **Linting:** `ruff` with config in `ruff.toml`. `E501` is off (a few long single-line expressions in `main.py` read better unwrapped) and `fastapi.Depends`/`fastapi.Security` are exempt from `B008`, which flags the standard FastAPI idiom as a mutable-default bug.
- **Coverage floor:** `pytest --cov-fail-under=75`, against a current 80%.
- **Dependabot:** Weekly updates for pip, GitHub Actions, and the Dockerfile base image.

### Security
- **Base image un-pinned to the minor version:** `python:3.12.4-slim` → `python:3.12-slim`. This partially reverses the v0.6.0 decision to pin to a patch tag. That pin achieved reproducibility but froze the entire OS layer at its publication date; two years on, Trivy found **48 fixable HIGH/CRITICAL CVEs (6 CRITICAL)** in Debian 12.6 packages. Moving up one level takes that to 0 while keeping the Python minor version pinned, and Dependabot's `docker` ecosystem now watches the tag so the same drift is caught rather than accumulating silently.
- **Runtime dependencies upgraded to clear starlette CVEs:** `fastapi` 0.111.0 → 0.141.1 (and the rest of `requirements.txt` re-pinned to match). `fastapi==0.111.0` constrained `starlette` to `<0.38.0`, holding three HIGH CVEs in place — including **CVE-2024-47874**, a `multipart/form-data` denial of service reachable on any proxied `POST`. This crosses a starlette major version (0.37 → 1.4); the full test suite and a container smoke test (config load, health, readiness, metrics, auth rejection) both pass on the new stack.
- **Dev dependencies upgraded:** `pytest` 8.2.2 → 9.1.1, resolving `PYSEC-2026-1845`, plus matching `pytest-asyncio` and `pytest-cov`.
- **Least-privilege workflow permissions:** default `contents: read`, with only the `publish` job widening to `packages: write`.

### Changed
- **Image built once, then scanned and published:** the `image` job builds with `load: true` so Trivy scans the exact artifact `publish` pushes, and a shared GitHub Actions layer cache makes the publish step a cache hit rather than a genuine second build.
- **Concurrency group:** a newer push supersedes an in-flight run on the same ref, except on `main`, where runs publish and are never cancelled.
- **Error chaining:** the three proxy exception handlers now `raise HTTPException(...) from e`, preserving the original traceback for debugging without changing the client-facing response.
- **Documentation:** added a CI/CD section to [Troubleshooting](TROUBLESHOOTING.md) covering each failure mode hit while building the pipeline, and rewrote the README's CI/CD section as a table of the six gates.

---

## v0.7.1 — CI Import Fix (2026-07-29)

### Fixed
- **CI test collection:** `pytest` in GitHub Actions failed with `ModuleNotFoundError: No module named 'src'`. Cause: the CI workflow invokes the bare `pytest` command, which — unlike `python -m pytest` — does not add the repo root to `sys.path`, so `from src.main import app` in `tests/test_api.py` couldn't resolve. Fixed by adding `pytest.ini` with `pythonpath = .`, which makes the repo root importable for every invocation style (bare `pytest`, `python -m pytest`, CI, local) without adding a packaging system (`pyproject.toml`/`setup.py`) or a `sys.path` hack in the tests themselves.

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
