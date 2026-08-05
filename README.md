# Universal API Gateway 🚀

<p align="center">
  <img alt="Tech stack: Python 3.12, FastAPI, Uvicorn, httpx, YAML, Docker, Kubernetes, GitHub Actions, pytest, Prometheus" src="https://github-readme-tech-stack.vercel.app/api/cards?title=Tech%20Stack&theme=github_dark&align=center&titleAlign=center&width=470&gap=12&lineHeight=8&fontSize=18&hideBg=true&borderRadius=6&border=%2330363d&titleColor=%238b949e&lineCount=3&line1=python,Python%203.12,auto;fastapi,FastAPI,auto;,Uvicorn,auto;,httpx,auto;&line2=yaml,YAML,auto;docker,Docker,auto;kubernetes,Kubernetes,auto;&line3=githubactions,GitHub%20Actions,auto;pytest,pytest,auto;prometheus,Prometheus,auto;" />
</p>

> A YAML-configured reverse proxy for third-party APIs, packaged as a Docker container with a Kubernetes deployment path. "Self-healing" here means what it means for any stateless K8s Deployment: crashed pods get restarted by Kubernetes, not by application logic.

---

## 🎯 What it does

A reverse proxy that turns a YAML file into a set of API routes. Define an upstream API and its routes in `config/gateway.yaml`; the FastAPI app reads that file on startup and dynamically registers a matching proxy route for each entry — no Python code changes needed to add or remove an upstream.

```mermaid
graph LR
    %% Nodes
    External["🤖 External Automation\n(n8n, CI/CD, CronBots)"]
    K8s["⚙️ Gateway Pods\n(Port 30000)"]
    Config["📌 config/gateway.yaml\n(Your API Definitions)"]
    Provider["🌍 Any External API\n(Weather, Finance, etc.)"]

    %% Connections
    External <-->|"HTTP / REST"| K8s
    Config -.->|"Dynamically Configures"| K8s
    K8s <-->|"Async Proxy Fetch"| Provider

    %% Styling
    style External fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:#fff
    style K8s fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff
    style Config fill:#e67e22,stroke:#d35400,stroke-width:2px,color:#fff
    style Provider fill:#f1c40f,stroke:#f39c12,stroke-width:2px,color:#333
```

---

## 🛠️ Core SRE Features

| Feature | Description |
|---|---|
| **Authentication** | Opt-in Bearer token protection for proxy routes (`API_AUTH_TOKEN`). Health probes remain safely unauthenticated. |
| **Rate Limiting** | 100 req/min per route. Returns standard `429 Too Many Requests` (in-memory, scaled per pod). |
| **Idempotent Retries** | Automatic exponential backoff (up to 3x) for `GET`/`HEAD` requests on `502`/`503`/`504` upstream failures. |
| **Prometheus Metrics** | High-cardinality safe `/metrics` endpoint tracking request latency and volume natively. |
| **Graceful Shutdown** | Zero-downtime termination via FastAPI `lifespan` connection management. |
| **Structured Logging** | Built-in key/value observability (`request_id`, `method`, `path`, `status`, `duration_ms`). |
| **Health Probes** | Explicit `/healthz` (liveness) and `/readyz` (readiness) endpoints. |
| **Container Hardening** | Runs as non-root (`UID 1000`) on a read-only filesystem with dropped capabilities. |

See [`docs/CHANGELOG.md`](docs/CHANGELOG.md) for detailed implementation notes.

---

## 📂 Repository Structure

```text
📦 universal-api-gateway/
│
├── 📁 config/
│   └── 📄 gateway.yaml       # 👈 99% of your edits happen here
│
├── 📁 enterprise-k8s/        # Kubernetes manifests for production
│
├── 📁 src/
│   └── 🐍 main.py            # Core Python proxy engine
│
├── 📁 tests/
│   └── 🧪 test_api.py        # Pytest smoke suite (auth, probes, rate limit)
│
├── 📁 docs/                  # Architecture & troubleshooting guides
├── ⚙️ start.bat              # One-click local startup
├── 📄 .env.example           # Environment variable template — copy to .env
├── 📄 requirements.txt       # Runtime dependencies (pinned)
├── 📄 requirements-dev.txt   # Test-only dependencies (not shipped in the image)
├── 🐳 Dockerfile
└── 🐳 docker-compose.yml
```

### Environment Variables

| Variable | Default | Effect |
|---|---|---|
| `CONFIG_PATH` | `config/gateway.yaml` | Path to the gateway config file. |
| `ALLOWED_ORIGINS` | `http://localhost,http://localhost:30000` | Comma-separated CORS allow-list. |
| `API_AUTH_TOKEN` | *(unset)* | Bearer token required on proxy routes. Unset = auth disabled (startup warning logged). |

Copy `.env.example` to `.env` and edit it — `docker-compose.yml` loads it automatically.

---

## 📌 Usage: "Fill in the Blanks"

> [!IMPORTANT]  
> **Do NOT edit `src/main.py`** unless extending the core engine. Just define your APIs in `config/gateway.yaml` and let the engine handle the rest.

**Example `config/gateway.yaml`:**
```yaml
gateways:
  - name: "weather"
    base_url: "https://api.open-meteo.com/v1"
    routes:
      - path: "/current"
        method: "GET"
        target_path: "/forecast?latitude=52.52&longitude=13.41&current=temperature_2m"
```
Registers a proxy route at `http://localhost:30000/api/weather/current`. It's open by default — set `API_AUTH_TOKEN` (see [Environment Variables](#environment-variables)) if it needs to require a Bearer token.

---

## 🚀 Quickstart

### Local Development (Easy Mode)
1. Ensure **Docker Desktop** is running.
2. Edit `config/gateway.yaml` with your target APIs.
3. Optional: copy `.env.example` to `.env` and set `API_AUTH_TOKEN` if you want proxy routes protected.
4. Run `start.bat`.
5. Visit `http://localhost:30000/docs` for the generated Swagger UI, or `http://localhost:30000/metrics` for Prometheus metrics.

### Production (Kubernetes)
For production clusters, use the raw manifests in `enterprise-k8s/`.

```bash
docker build -t universal-api-gateway:latest .
kubectl apply -k .
```

#### 🛡️ Verifying K8s Manifests (Dry Run)
Verify manifests compile correctly without deploying:
```bash
kubectl kustomize .
```
*(Prints the rendered YAML to your terminal).*

---

## 📚 Documentation
- [Architecture Overview](docs/ARCHITECTURE.md) — How the 3-Tier engine is mapped.
- [K8s Infrastructure](enterprise-k8s/README.md) — How K8s is being utilized here.
- [Engine Guide](src/README.md) — Details on the `main.py` Python proxy.
- [Troubleshooting](docs/TROUBLESHOOTING.md) — Infrastructure debugging and port collision fixes.
- [Changelog](docs/CHANGELOG.md) — Release notes.
- [Future Roadmap](docs/FUTURE_ROADMAP.md) — Upcoming enterprise features (HPA, PDB, CI/CD scanning).

---

## ⚙️ CI/CD Pipeline

GitHub Actions runs on every push/PR to `main`: install dependencies → run the `pytest` smoke suite (`tests/test_api.py`) → build the Docker image (dry run, not pushed). A failing test blocks the build step. Run the same suite locally with:
```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
