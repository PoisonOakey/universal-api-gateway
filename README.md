# Universal API Gateway 🚀

<p align="center">
  <img alt="Tech stack: Python 3.12, FastAPI, Uvicorn, httpx, YAML, Docker, Kubernetes, GitHub Actions, pytest, Prometheus" src="https://github-readme-tech-stack.vercel.app/api/cards?title=Tech%20Stack&theme=github_dark&align=center&titleAlign=center&width=470&gap=12&lineHeight=8&fontSize=18&hideBg=true&borderRadius=6&border=%2330363d&titleColor=%238b949e&lineCount=3&line1=python,Python%203.12,auto;fastapi,FastAPI,auto;,Uvicorn,auto;,httpx,auto;&line2=yaml,YAML,auto;docker,Docker,auto;kubernetes,Kubernetes,auto;&line3=githubactions,GitHub%20Actions,auto;pytest,pytest,auto;prometheus,Prometheus,auto;" />
</p>

> Third-party APIs behind one container, so the systems calling them never hardcode an upstream URL, a retry, or a rate limit.

---

## 🎯 What it does

A reverse proxy that turns a YAML file into API routes. List an API in `config/gateway.yaml` and the gateway serves a matching endpoint for it. Adding or removing one is an edit and a restart — no Python.

```mermaid
graph LR
    %% Nodes
    External["🤖 External Automation<br/>(n8n, CI/CD, CronBots)"]
    K8s["⚙️ Gateway Pods<br/>(Port 30000)"]
    Config["📌 config/gateway.yaml<br/>(Your API Definitions)"]
    Provider["🌍 Any External API<br/>(Weather, Finance, etc.)"]

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

The image is pulled from the GitHub Container Registry (GHCR) by tag with **no pull secret**, because the package CI publishes is public.

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

---

## 🧱 From Commit to Cluster

How the image above got onto that cluster — five lanes, each owned by the tool that should own it.

This covers **delivery**. For what happens to a single request once the pods are up — async proxying, retries, rate limiting — see [The Request Lifecycle](docs/ARCHITECTURE.md#-the-request-lifecycle).

```mermaid
flowchart TD
    classDef ci fill:#e6f3ff,stroke:#0066cc,stroke-width:2px,color:#003366;
    classDef tf fill:#f3e8ff,stroke:#7c3aed,stroke-width:2px,color:#3b0764;
    classDef kz fill:#e6ffe6,stroke:#009933,stroke-width:2px,color:#004d1a;
    classDef run fill:#fff4e6,stroke:#cc6600,stroke-width:2px,color:#663300;
    classDef dk fill:#e0f7fa,stroke:#00796b,stroke-width:2px,color:#004d40;

    style Source fill:#ffffff,stroke:#dee2e6,stroke-width:2px,stroke-dasharray: 5 5,color:#333
    style Build fill:#ffffff,stroke:#dee2e6,stroke-width:2px,stroke-dasharray: 5 5,color:#333
    style Provision fill:#ffffff,stroke:#dee2e6,stroke-width:2px,stroke-dasharray: 5 5,color:#333
    style Deploy fill:#ffffff,stroke:#dee2e6,stroke-width:2px,stroke-dasharray: 5 5,color:#333
    style Serve fill:#ffffff,stroke:#dee2e6,stroke-width:2px,stroke-dasharray: 5 5,color:#333

    subgraph Source [One Dockerfile -- two destinations]
        direction LR
        S["Dockerfile"]:::dk --> L["docker compose up<br/>your machine, :30000"]:::dk
    end

    subgraph Build [Build &amp; Publish -- GitHub Actions]
        direction LR
        A["lint · tests · deps<br/>infra · secrets · image"]:::ci --> B["publish<br/>needs: all six"]:::ci
        B --> C["GHCR package<br/>tagged by commit SHA"]:::ci
    end

    subgraph Provision [Provision -- Terraform, run by hand]
        direction LR
        D["terraform/aks"]:::tf --> F["Cluster<br/>+ kubeconfig"]:::tf
    end

    subgraph Deploy [Deploy -- Kustomize, run by hand]
        direction LR
        G["base<br/>gateway.yaml becomes a ConfigMap"]:::kz --> H["overlays/cloud<br/>base and image pinned to one SHA"]:::kz
    end

    subgraph Serve [Serve -- left running on the cluster]
        direction LR
        I["Gateway pods<br/>non-root, read-only fs"]:::run --> J["/healthz + /readyz<br/>answered to the kubelet"]:::run
        I --> K["/metrics<br/>gateway_requests_total"]:::run
    end

    S --> A
    C --> H
    F --> G
    H --> I
```

**One `Dockerfile`, two destinations.** On your machine, `docker compose up` builds it and stops — no registry, no cluster. Through CI, the same file clears six checks and lands in GHCR tagged with the commit SHA (Secure Hash Algorithm) — the unique fingerprint git gives every commit.

**Putting that image on a cluster takes three steps, all run by hand:**

1. `terraform apply` — creates the cluster and writes your kubeconfig
2. `kubectl apply -k k8s/overlays/cloud` — renders the manifests and sends them
3. the pods start, answer their probes, and begin serving

**CI stops at the registry.** A green pipeline means an image was published — not that anything was deployed. That gap is deliberate.

**What the overlay changes.** Kustomize works in layers: a *base* describes the app, and an *overlay* patches it for one environment. Three things differ.

| | Base | `overlays/cloud` |
|---|---|---|
| **Reachable how** | `NodePort` — only on the node's own port | `LoadBalancer` — gets a public IP |
| **Image from** | built on your machine | pulled from GHCR |
| **Which version** | `latest` | one specific commit SHA |

The last row is the one that matters. Manifests and image are pinned to the **same** SHA, so a single value describes everything that got deployed — instead of a manifest version and an image version that can quietly drift apart.

---

## 🛠️ Key Engineering Decisions

| Feature | Description |
|---|---|
| **Asynchronous I/O** | While one request waits on a slow provider, the same worker keeps serving everyone else. A degraded upstream costs latency, not the capacity to answer other traffic. |
| **Authentication** | Set `API_AUTH_TOKEN` and every proxy route demands it. Health checks stay open, because Kubernetes has no way to send a token. |
| **Rate Limiting** | 100 requests a minute per caller, then a `429`. Each pod counts on its own, so three pods allow 300. |
| **Idempotent Retries** | When an upstream API times out or returns a `502`/`503`/`504`, reads are tried again — three attempts, waiting longer between each. Writes are never retried, so nothing is submitted twice. |
| **Prometheus Metrics** | `/metrics` counts and times every request by method, path and status. Rejections are counted too, not just the calls that worked. |
| **Graceful Shutdown** | When the pod stops, the gateway closes its upstream connections instead of leaving them hanging. |
| **Structured Logging** | One line per request — an ID, the method, path, status and how long it took. Readable in a terminal, parseable by anything you ship it to. |
| **Health Probes** | `/healthz` says the process is alive. `/readyz` says it can take traffic. Kubernetes restarts or reroutes based on the answers. |
| **Container Hardening** | Runs as an ordinary user, not root, and cannot write to its own filesystem. A compromised proxy has nothing to tamper with. |

Implementation notes are in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

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
> **Do NOT edit `src/main.py`** unless you are extending the engine itself.

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

#### 🛡️ Dry Run
Verify the manifests compile without deploying:
```bash
kubectl kustomize .
```
*(Prints the rendered YAML to your terminal).*

---

## 📚 Documentation
- [Architecture Overview](docs/ARCHITECTURE.md) — The three layers, and the request lifecycle step by step.
- [K8s Infrastructure](k8s/README.md) — How K8s is being utilized here.
- [Engine Guide](src/README.md) — Details on the `main.py` Python proxy.
- [Troubleshooting](docs/TROUBLESHOOTING.md) — Infrastructure debugging, port collision fixes, and CI/CD gate failures.
- [Changelog](docs/CHANGELOG.md) — Release notes.
- [Future Roadmap](docs/FUTURE_ROADMAP.md) — Planned features, and what is deliberately not built yet.

---

## ⚙️ CI/CD Pipeline

Six gates in parallel on every push and PR to `main`. All six must pass before the image reaches GHCR.

| Gate | What it checks |
| :--- | :--- |
| **Lint** | `ruff check` over `src/` and `tests/` |
| **Tests** | `pytest` with coverage, floored at 75% |
| **Dependency audit** | `pip-audit` over both requirements files, failing on a known CVE |
| **Validate infrastructure** | `terraform validate` for AKS, `kustomize build` for base and cloud, then `kubeconform` against real Kubernetes schemas |
| **Secret scan** | `gitleaks` across the full history, not just the tip |
| **Build & scan image** | Trivy, blocking on any fixable HIGH or CRITICAL |

Dependabot proposes updates weekly for pip, Actions, and the base image.

Worth running before you push:

```bash
ruff check src tests
pytest --cov=src --cov-report=term-missing
pip-audit -r requirements.txt -r requirements-dev.txt
```

CI never creates a cluster or deploys to one. A green check means the image is publishable — not that anything is running.

When a gate fails, [Troubleshooting → CI/CD](docs/TROUBLESHOOTING.md#cicd-github-actions) has the root cause for each.
