from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import yaml
import os

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  App Init
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
app = FastAPI(
    title="Universal API Gateway",
    description="A containerized, self-healing, config-driven API gateway.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  Config Loading & Dynamic Routing
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CONFIG_PATH = os.getenv("CONFIG_PATH", "../config/gateway.yaml")
if not os.path.exists(CONFIG_PATH):
    # Fallback for local testing
    CONFIG_PATH = "config/gateway.yaml"

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load config from {CONFIG_PATH}: {e}")
        return {}

gateway_config = load_config()
client = httpx.AsyncClient()

def create_proxy_endpoint(gateway_name, base_url, target_path, method):
    async def proxy_endpoint(request: Request):
        try:
            # Reconstruct the target path by injecting path params
            # e.g., if target_path is "/products/{id}" and path_params has id=5
            formatted_target = target_path
            for key, val in request.path_params.items():
                formatted_target = formatted_target.replace(f"{{{key}}}", str(val))
                
            target_url = f"{base_url.rstrip('/')}/{formatted_target.lstrip('/')}"
            
            # Forward the request
            req_kwargs = {
                "method": method,
                "url": target_url,
                "params": request.query_params,
                "headers": {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
            }
            if method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    req_kwargs["content"] = body
            
            response = await client.request(**req_kwargs)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Bad Gateway ({gateway_name}): {str(e)}")
            
    return proxy_endpoint

if "gateways" in gateway_config and gateway_config["gateways"]:
    for gw in gateway_config["gateways"]:
        gw_name = gw.get("name", "unknown")
        base_url = gw.get("base_url")
        
        for route in gw.get("routes", []):
            path = f"/api/{gw_name}{route['path']}"
            method = route.get("method", "GET").upper()
            target_path = route.get("target_path")
            desc = route.get("description", f"Proxy route for {gw_name}")
            
            # Register route dynamically
            app.add_api_route(
                path,
                create_proxy_endpoint(gw_name, base_url, target_path, method),
                methods=[method],
                tags=[gw_name.capitalize()],
                description=desc
            )

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  Health Check
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Universal API Gateway",
        "status": "running",
        "gateways_loaded": len(gateway_config.get("gateways", [])),
        "docs": "/docs",
    }
