# Architecture Overview

This document provides a high-level overview of the entire Gateway ecosystem. If you are trying to understand how all the folders and systems communicate, this is the map.

---

## 🏗️ The 3-Tier Architecture

The repository is intentionally split into three distinct layers to ensure a clean Separation of Concerns (SoC).

```mermaid
graph TD
    %% Layers
    subgraph "Layer 1: Configuration (config/)"
        YAML["📄 gateway.yaml<br/>User-defined APIs"]
    end
    
    subgraph "Layer 2: Execution Engine (src/)"
        Python["🐍 main.py<br/>(FastAPI + HTTPX)"]
    end
    
    subgraph "Layer 3: Infrastructure (Deployment)"
        Docker["🐳 Docker / start.bat<br/>(Local Easy Mode)"]
        K8s["☸️ k8s/<br/>(Kubernetes)"]
    end

    %% Flow
    YAML -->|"Parsed dynamically by"| Python
    Python -->|"Packaged and run by"| Docker
    Python -->|"Orchestrated by"| K8s
    YAML -.->|"Injected via ConfigMap into"| K8s
```

### Layer 1: Configuration (`config/`)
This is the **Control Plane**. It contains the `gateway.yaml` file. This layer exists so that normal users never have to touch code. They define what APIs they want to use here, and the rest of the system obeys.

### Layer 2: Execution Engine (`src/`)
This is the **Data Plane**. It contains `main.py` — reads the config layer and generates the proxy routes from it. Backend work here means: connection lifecycle (the shared `httpx` client), timeouts/retries, request logging and metrics, auth/CORS, and — not yet built — response caching.

### Layer 3: Infrastructure (`k8s/` & Docker)
This is the **Hosting Plane**. It determines *where* the engine runs. 
- The `docker-compose.yml` (and `start.bat`) provide an easy local hosting environment.
- The `k8s/` folder provides the declarative YAML needed to deploy the engine to a Kubernetes cluster (with strict non-root and read-only filesystem security constraints).

---

## 🚚 The Delivery Path

The three layers above describe what the repository holds. This is how it reaches a cluster — five lanes, each owned by the tool that should own it.

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

**One `Dockerfile`, two destinations.** On your machine, `docker compose up` builds it and stops — no registry, no cluster. Through CI, the same file clears six checks and lands in the GitHub Container Registry (GHCR), tagged with the commit SHA.

**Putting that image on a cluster takes three steps, all run by hand:**

1. `terraform apply` — creates the cluster and writes your kubeconfig
2. `kubectl apply -k k8s/overlays/cloud` — renders the manifests and sends them
3. the pods start, answer their probes, and begin serving

**CI stops at the registry.** Nothing under `.github/` runs `terraform apply` or `kubectl apply`. The infrastructure gate proves the Terraform parses and the manifests build against real Kubernetes schemas, then the pipeline publishes an image and ends. A green check means the configuration is valid, not that anything was deployed.

**What the overlay changes.** Kustomize works in layers: a *base* describes the app, and an *overlay* patches it for one environment. Three things differ.

| | Base — `kubectl apply -k .` at the repo root | `overlays/cloud` |
|---|---|---|
| **Reachable how** | `NodePort` — only on the node's own port | `LoadBalancer` — gets a public IP |
| **Image from** | built on your machine | pulled from GHCR |
| **Which version** | `latest` | one specific commit SHA |

The last row is the one that matters. `overlays/cloud` pulls its base from `github.com/PoisonOakey/universal-api-gateway//?ref=<sha>` and sets `newTag` to that same SHA, so a single value describes everything that got deployed — instead of a manifest revision and an image revision that can quietly drift apart. The tradeoff is that bumping the deployed version means editing two lines in one file, and they must match.

---

## 🔄 The Request Lifecycle

When a piece of external automation (like n8n or a cron job) makes a request to the Gateway, this is the exact flow:

1. **Ingress:** The request hits the Kubernetes `NodePort` (or Docker port) at `:30000`.
2. **Routing & CORS:** FastAPI handles CORS preflight checks and matches the URL path against the routes it dynamically generated during startup.
3. **Authentication:** For proxy routes, FastAPI verifies the `Authorization: Bearer <token>` header against the `API_AUTH_TOKEN` environment variable. If missing or invalid, it rejects the request (401).
4. **Rate Limiting:** The `slowapi` decorator checks the client IP against the per-route limit (`100/min`). If exceeded, it rejects the request with a `429 Too Many Requests`.
5. **Proxy & Retry:** The `httpx` async client intercepts the request and forwards the payload to the external provider. If the upstream fails with a `502`, `503`, or `504` on a safe method (`GET`/`HEAD`), `tenacity` retries the request using exponential backoff.
6. **Metrics:** Latency and status codes are recorded into Prometheus metrics registries for real-time observability.
7. **Egress:** The upstream response is piped directly back to the automation tool.
