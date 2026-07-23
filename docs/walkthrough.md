# Walkthrough — Financial Middleware API

---

## What Did Docker Actually Do?

Think of it like cooking:

```
Your Code (main.py, api/)    = Your recipe
requirements.txt              = Your ingredient list
Dockerfile                    = Instructions for a robot chef
Docker Image (finance-api)    = A sealed lunchbox with the finished meal inside
Docker Container              = Opening the lunchbox and eating it
```

Without Docker, you would need to:
1. Install Python 3.12
2. Install pip
3. Run `pip install fastapi uvicorn yfinance pandas`
4. Hope nothing conflicts with your existing Python setup
5. Run the server manually

With Docker, you just do:
1. `docker build -t finance-api .`
2. `docker run -p 9000:8000 finance-api`
3. Done. Everything works identically on any machine.

**That's the entire point of Docker.** It eliminates "but it works on my machine" problems.

---

## Step 1: Audit the Code

Read these files in this order:

| Order | File | What it does |
|---|---|---|
| 1 | `docs/api_documentation.md` | The full API contract — read this first |
| 2 | `src/main.py` | The app entry point — see how routes are wired |
| 3 | `src/api/routes/stocks.py` | The core stock endpoint — calls yfinance |
| 4 | `src/api/routes/watchlist.py` | Watchlist CRUD — in-memory storage |
| 5 | `src/api/routes/alerts.py` | Pattern alerts CRUD — in-memory storage |
| 6 | `src/api/models/alerts.py` | Data validation — see allowed pattern types |
| 7 | `Dockerfile` | How everything gets packaged |

---

## Step 2: Run It Locally (Without Docker)

```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8000
```
Then open `http://localhost:8000/docs` in your browser to test.

---

## Step 3: Run It With Docker

```bash
docker build -t finance-api .
docker run -d -p 9000:8000 finance-api
```
Then open `http://localhost:9000/docs` in your browser to test.

---

## Step 4: Test These Endpoints

**Test 1 — Get stock price:**
```
GET http://localhost:9000/api/v1/stock/AAPL
```
Expected: Real-time AAPL price from Yahoo Finance.

**Test 2 — Add to watchlist:**
```
POST http://localhost:9000/api/v1/watchlist
Body: { "user_id": "test_user", "symbol": "TSLA" }
```
Expected: Success message with a watchlist ID.

**Test 3 — Set pattern alert:**
```
POST http://localhost:9000/api/v1/pattern-alerts
Body: { "user_id": "test_user", "symbol": "NVDA", "pattern_type": "golden_cross", "sensitivity": "high" }
```
Expected: Success message with an alert ID.

**Test 4 — Get stock history (for charts):**
```
GET http://localhost:9000/api/v1/stock/DIS/history?period=1mo
```
Expected: Array of daily OHLCV data for Disney.

---

## What Happens Next: Infrastructure & Econophysics

Now that the code is container-ready, the next steps are to build out the Kubernetes infrastructure and refine the economic models.

```text
 PHASE 1 (Done)        PHASE 2 (Done)         PHASE 3 (Next)           PHASE 4
┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
│  Build the   │   │  Containerize│   │  Kubernetes      │   │  Refine      │
│  FastAPI     │──►│  with Docker │──►│  Deployment      │──►│  Econophysics│
│  Middleware  │   │  (Portable)  │   │  (K8s Manifests) │   │  Algorithms  │
└──────────────┘   └──────────────┘   └──────────────────┘   └──────────────┘
```

### Phase 3: Infrastructure (Kubernetes)
1. **Write Manifests:** Create `deployment.yaml` and `service.yaml` inside a future `k8s/` folder.
2. **Local Cluster Test:** Run the container locally using Minikube or Docker Desktop's Kubernetes cluster.
3. **CI/CD Pipeline:** Add GitHub Actions to automatically build the Docker image and push it to a container registry.

*(Note: The core Econophysics algorithms are developed and maintained in a separate engine repository. This repository will remain strictly focused on API routing and documentation.)*
