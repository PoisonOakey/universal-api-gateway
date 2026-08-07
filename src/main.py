import logging
import os
import re
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from urllib.parse import urlsplit, urlunsplit

import httpx
import yaml
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

# ──────────────
#  Logging Setup
# ──────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s level=%(levelname)s %(message)s")
logger = logging.getLogger("gateway")

# ──────────────
#  App Init
# ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=30.0)
    app.state.client = httpx.AsyncClient(timeout=timeout)
    yield
    await app.state.client.aclose()

app = FastAPI(
    title="Universal API Gateway",
    description="A containerized, config-driven API gateway.",
    version="0.2.0",
    lifespan=lifespan,
)

# ──────────────
#  Rate Limiting
# ──────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ──────────────
#  Metrics
# ──────────────
REQUESTS_TOTAL = Counter(
    "gateway_requests_total",
    "Total HTTP requests to the gateway",
    ["method", "path", "status"]
)
REQUEST_DURATION = Histogram(
    "gateway_request_duration_seconds",
    "Gateway HTTP request duration in seconds",
    ["method", "path"]
)

ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost,http://localhost:30000").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        duration_s = time.time() - start_time
        duration_ms = int(duration_s * 1000)
        logger.info(f"request_id={request_id} method={request.method} path={request.url.path} status={status_code} duration_ms={duration_ms}")

        route = request.scope.get("route")
        path_label = route.path if route else request.url.path
        REQUESTS_TOTAL.labels(method=request.method, path=path_label, status=status_code).inc()
        REQUEST_DURATION.labels(method=request.method, path=path_label).observe(duration_s)

    return response

# ──────────────
#  Config Loading & Dynamic Routing
# ──────────────
CONFIG_PATH = os.getenv("CONFIG_PATH", "../config/gateway.yaml")
if not os.path.exists(CONFIG_PATH):
    # Fallback for local testing
    CONFIG_PATH = "config/gateway.yaml"

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Warning: Could not load config from {CONFIG_PATH}: {e}")
        return {}

gateway_config = load_config()

# ──────────────
#  Authentication
# ──────────────
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")
if not API_AUTH_TOKEN:
    logger.warning("AUTH DISABLED: set API_AUTH_TOKEN to protect proxy routes")

auth_scheme = HTTPBearer(auto_error=False)

async def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    if not API_AUTH_TOKEN:
        return None
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    if not secrets.compare_digest(credentials.credentials, API_AUTH_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid token")

def create_proxy_endpoint(gateway_name, base_url, target_path, method):
    should_retry = method in ["GET", "HEAD"]

    async def proxy_endpoint(request: Request):
        try:
            # Reconstruct the target path by injecting path params
            formatted_target = target_path
            for key, val in request.path_params.items():
                formatted_target = formatted_target.replace(f"{{{key}}}", str(val))

            target_url = f"{base_url.rstrip('/')}/{formatted_target.lstrip('/')}"

            # A target_path may carry its own query string -- the documented way
            # to pin upstream arguments, e.g. "/forecast?latitude=52.52". httpx
            # *replaces* a URL's query with whatever `params` is given rather
            # than merging, so passing the caller's query params straight
            # through wiped the configured ones whenever the caller sent none.
            # Merge them explicitly, and let the caller win on a conflict so a
            # configured value stays a default rather than a hard-coded answer.
            split_target = urlsplit(target_url)
            merged_params = httpx.QueryParams(split_target.query).merge(request.query_params)
            target_url = urlunsplit(split_target._replace(query=""))

            # Forward the request
            # Never forward the caller's credentials to the upstream: the bearer
            # token authenticates the caller to this gateway, not to the API behind it.
            drop_headers = ("host", "content-length", "authorization", "cookie")
            req_kwargs = {
                "method": method,
                "url": target_url,
                "params": merged_params,
                "headers": {k: v for k, v in request.headers.items() if k.lower() not in drop_headers}
            }
            if method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    req_kwargs["content"] = body

            async def make_request():
                return await request.app.state.client.request(**req_kwargs)

            if should_retry:
                make_request = retry(
                    wait=wait_exponential(multiplier=0.5, max=4),
                    stop=stop_after_attempt(3),
                    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)) | retry_if_result(lambda r: r.status_code in (502, 503, 504)),
                    before_sleep=lambda rs: logger.warning(f"gateway={gateway_name} event=retry attempt={rs.attempt_number} path={target_url}")
                )(make_request)

            upstream_response = await make_request()

            # Filter headers
            hop_by_hop = {"content-length", "content-encoding", "transfer-encoding", "connection"}
            filtered_headers = {
                k: v for k, v in upstream_response.headers.items()
                if k.lower() not in hop_by_hop
            }

            return Response(
                content=upstream_response.content,
                status_code=upstream_response.status_code,
                headers=filtered_headers
            )
        except httpx.TimeoutException as e:
            logger.error(f"gateway={gateway_name} error=TimeoutException detail={str(e)}")
            raise HTTPException(status_code=504, detail="Gateway Timeout") from e
        except httpx.RequestError as e:
            logger.error(f"gateway={gateway_name} error=RequestError detail={str(e)}")
            raise HTTPException(status_code=502, detail="Bad Gateway") from e
        except Exception as e:
            logger.error(f"gateway={gateway_name} error=Exception detail={str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error") from e

    # Unique name for slowapi route registration
    safe_target = re.sub(r'[^a-zA-Z0-9_]', '_', target_path)
    proxy_endpoint.__name__ = f"proxy_{gateway_name}_{safe_target}"
    proxy_endpoint.__qualname__ = proxy_endpoint.__name__

    return limiter.limit("100/minute")(proxy_endpoint)

if "gateways" in gateway_config and gateway_config["gateways"]:
    for gw in gateway_config["gateways"]:
        gw_name = gw.get("name", "unknown")
        base_url = gw.get("base_url")

        for route in gw.get("routes", []):
            path = f"/api/{gw_name}{route['path']}"
            method = route.get("method", "GET").upper()
            target_path = route.get("target_path")
            desc = route.get("description", f"Proxy route for {gw_name}")

            # Register route dynamically with auth dependency
            app.add_api_route(
                path,
                create_proxy_endpoint(gw_name, base_url, target_path, method),
                methods=[method],
                tags=[gw_name.capitalize()],
                description=desc,
                dependencies=[Depends(verify_auth)]
            )

# ──────────────
#  Health Checks
# ──────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Universal API Gateway",
        "status": "running",
        "gateways_loaded": len(gateway_config.get("gateways", [])),
        "docs": "/docs",
    }

@app.get("/healthz", tags=["Health"])
def healthz():
    return {"status": "ok"}

@app.get("/readyz", tags=["Health"])
def readyz(request: Request):
    # Checking for any registered api route
    routes = [r for r in request.app.routes if r.path.startswith("/api/")]
    if len(routes) > 0:
        return {"status": "ready", "routes_loaded": len(routes)}
    raise HTTPException(status_code=503, detail="Gateway config not loaded or no routes registered")

@app.get("/metrics", tags=["Metrics"])
def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
