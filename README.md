# Econophysics API Interface

> A lightweight FastAPI middleware and documentation hub for our Econophysics trading system.

---

## 🎯 Project Scope
To be completely clear: **This repository is strictly an API interface.** 

The heavy lifting—the actual thermodynamic market calculations, Shannon entropy processing, and complex economic modeling—lives in a separate, dedicated engine repository. 

This project serves two specific purposes:
1. **API Gateway:** A FastAPI layer that safely exposes the underlying econophysics engine to our frontend applications.
2. **Documentation Hub:** The single source of truth for our API contracts, payloads, and endpoint structures.

---

## 🚀 What This API Exposes
* **Econophysics Alerts:** Endpoints for the frontend to subscribe to structural market entropy drops.
* **Transfer Entropy Mapping:** Endpoints to fetch causal information flows between SEA assets.
* **Market Data:** Standardized RESTful routing for Yahoo Finance data.

---

## ⚙️ Architecture

```mermaid
graph LR
    %% Nodes
    Frontend["💻 Frontend Client"]
    API["⚡ FastAPI Interface\n(This Repo)"]
    Engine["🧠 Core Econophysics Engine\n(External Repo)"]
    YF["📊 Yahoo Finance"]

    %% Connections
    Frontend <-->|"HTTP / REST"| API
    API <-->|"Internal RPC"| Engine
    API <-->|"Data Fetch"| YF

    %% Styling
    style Frontend fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:#fff
    style API fill:#3498db,stroke:#2980b9,stroke-width:3px,color:#fff
    style Engine fill:#9b59b6,stroke:#8e44ad,stroke-width:2px,color:#fff
    style YF fill:#f1c40f,stroke:#f39c12,stroke-width:2px,color:#333
```

---

## 📁 Repository Structure
```text
.
├── src/                    # Source code
│   ├── api/                # API routing logic
│   └── main.py             # Application entry point
├── docs/                   # Documentation
│   ├── api_documentation.md
│   └── walkthrough.md
├── tests/                  # API endpoint unit tests
├── Dockerfile              # Container definition for the API
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 📚 API Documentation
For full technical details, HTTP methods, and JSON payload schemas, please see the [API Documentation](docs/api_documentation.md).
