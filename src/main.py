from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import stocks, watchlist, alerts

# ─────────────────────────────────────────────
#  App Init
# ─────────────────────────────────────────────
app = FastAPI(
    title="Financial Middleware API",
    description=(
        "A middleware layer that connects your frontend to Yahoo Finance market data. "
        "Supports real-time stock pricing, OHLCV history, watchlists, and "
        "pattern-based trading alerts."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────
#  CORS — allow all origins for local dev
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  Routers
# ─────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(stocks.router, prefix=API_PREFIX)
app.include_router(watchlist.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)


# ─────────────────────────────────────────────
#  Health Check
# ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Financial Middleware API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
