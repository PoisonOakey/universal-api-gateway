# Universal API Gateway 🚀

<p align="center">
  <img alt="Tech stack: Python 3.12, FastAPI, Uvicorn, httpx, YAML, Docker, Kubernetes, GitHub Actions, pytest, Prometheus" src="https://github-readme-tech-stack.vercel.app/api/cards?title=Tech%20Stack&theme=github_dark&align=center&titleAlign=center&width=470&gap=12&lineHeight=8&fontSize=18&hideBg=true&borderRadius=6&border=%2330363d&titleColor=%238b949e&lineCount=3&line1=python,Python%203.12,auto;fastapi,FastAPI,auto;,Uvicorn,auto;,httpx,auto;&line2=yaml,YAML,auto;docker,Docker,auto;kubernetes,Kubernetes,auto;&line3=githubactions,GitHub%20Actions,auto;pytest,pytest,auto;prometheus,Prometheus,auto;" />
</p>

> A YAML-configured reverse proxy for third-party APIs, packaged as a plug-and-play container that deploys with Docker or Kubernetes so the systems calling it never hardcode upstream URLs, retries, or rate limits.

---

## 🎯 What it does

A reverse proxy that turns a YAML file into a set of API routes. List the APIs you want to reach in `config/gateway.yaml`, and on startup the gateway creates a matching endpoint on itself for each one. Adding or removing an API means editing that file and restarting — no Python involved.

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

## 📸 The Result

The same image, running in two places.

### 🐳 Locally, with Docker Compose

**Routes come from the config file, not from code.**

![Swagger UI listing the routes generated from config/gateway.yaml](docs/screenshots/docker-swagger.png)

Every route under **Weather** and **Dummy** exists because `config/gateway.yaml` declares it. No Python was written for any of them.

`/healthz`, `/readyz` and `/metrics` are built in, and the config cannot affect them.

<br>

**Auth is enforced, and every request is counted.**

![Terminal output showing health, auth rejection, two live proxied calls, and the metrics counter](docs/screenshots/docker-terminal.png)

| Request | Result |
|---|---|
| `GET /healthz` | `200` |
| Proxy call, no token | `401` — rejected |
| Proxy call, valid token | `200` — live data from Open-Meteo |
| `GET /api/dummy/products` | `200` — 30 products from dummyjson.com |

`gateway_requests_total` counts all four, labelled by method, path and status — **including the rejection**.

> A metric that only counts successes tells you nothing on the day something breaks.
---
### ☁️ On Azure Kubernetes Service

**Two nodes, two pods, one public IP.**

![Two AKS nodes, both pods Ready, the LoadBalancer public IP, live proxied calls and the metrics counter](docs/screenshots/aks-terminal.png)

Same four requests as above, this time against a `LoadBalancer` address reachable from the internet.

The image is pulled from GHCR by tag with **no pull secret**, because the package CI publishes is public.

<br>

**Three details worth more than the happy path:**

| What | Why it matters |
|---|---|
| Both pods landed on the **same node** | Two replicas survive a pod crash, not a node failure. Exactly what the anti-affinity row in [Not Built Yet](docs/FUTURE_ROADMAP.md) says. |
| The metrics are **one pod's view** | The LoadBalancer picks a backend per request, so scraping the Service returns whichever pod answered. Aggregating needs Prometheus scraping pods directly. |
| `/readyz` shows **hits nobody made** | The kubelet's readiness probes. First evidence the probes do anything at all. |

<br>

**The cluster, in the Azure portal.**

![The gateway-rg resource group in the Azure portal containing the AKS cluster](docs/screenshots/aks-portal.png)

Created by `terraform apply` from [`terraform/aks/`](terraform/aks/). Destroyed by `terraform destroy` in the same session.

**The cluster in this screenshot no longer exists.**

<br>

> **On naming.** The overlay applied here is [`k8s/overlays/gke`](k8s/overlays/gke/) — named for Google, but containing nothing Google-specific. A `LoadBalancer` Service and a GHCR image behave the same on either provider.
>
> [`terraform/gke/`](terraform/gke/) is written and validated but has **never been applied**; GCP billing was not available on this account. Azure is the path that has actually run.

---

## 🛠️ Key Engineering Decisions

| Feature | Description |
|---|---|
| **Authentication** | Opt-in Bearer token protection for proxy routes (`API_AUTH_TOKEN`). Health probes remain safely unauthenticated. |
| **Rate Limiting** | 100 req/min per route. Returns standard `429 Too Many Requests` (in-memory, scaled per pod). |
| **Idempotent Retries** | Automatic exponential backoff (up to 3x) for `GET`/`HEAD` requests on `502`/`503`/`504` upstream failures. |
| **Prometheus Metrics** | High-cardinality safe `/metrics` endpoint tracking request latency and volume natively. |
| **Graceful Shutdown** | The shared HTTP client is closed on FastAPI `lifespan` exit, releasing in-flight upstream connections. |
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
├── 📁 k8s/                   # Kubernetes manifests
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

### Kubernetes
To run it on a cluster, use the raw manifests in `k8s/`.

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
- [K8s Infrastructure](k8s/README.md) — How K8s is being utilized here.
- [Engine Guide](src/README.md) — Details on the `main.py` Python proxy.
- [Troubleshooting](docs/TROUBLESHOOTING.md) — Infrastructure debugging and port collision fixes.
- [Changelog](docs/CHANGELOG.md) — Release notes.
- [Future Roadmap](docs/FUTURE_ROADMAP.md) — Planned features, and what is deliberately not built yet.

---

## ⚙️ CI/CD Pipeline

GitHub Actions runs on every push/PR to `main`: install dependencies → run the `pytest` smoke suite (`tests/test_api.py`) → build the Docker image (dry run, not pushed). A failing test blocks the build step. Run the same suite locally with:
```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
