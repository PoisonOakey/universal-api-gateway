# Python Core Engine

This directory contains the Gateway's application code: `main.py`. It's a single file — there's no `src/api/`, `src/models/`, etc. to navigate.

> [!WARNING]
> **Do not edit `main.py` unless you are a backend developer.** 
> To add or modify API routes, you should edit `config/gateway.yaml` instead. The engine will automatically generate the routes for you.

---

## What does `main.py` actually do?

Unlike a traditional web app where each route (e.g. `/weather/current`) is a hardcoded Python function, every proxy route here is generated from config at startup.

Startup sequence:

1. **Initialization:** FastAPI app is created, Uvicorn serves it as an ASGI app.
2. **Config parse:** Reads `config/gateway.yaml`.
3. **Route generation:** For each route entry in the YAML, registers a FastAPI endpoint that forwards matching requests to the configured `base_url` via a shared `httpx.AsyncClient`.
4. **Proxying (per request):** Substitutes path params, forwards method/headers/body/query string to the upstream, applies retry logic (if `GET`/`HEAD`), and returns the upstream's status/body/headers back to the caller.

## Why abstract it?

Routes come from `config/gateway.yaml`, not hardcoded Python, so:
- Adding or changing an upstream API doesn't require touching this file.
- Changes to `main.py` (e.g. adding Redis caching — the one piece not yet built) affect every configured route at once, instead of being duplicated per-route.

## What's already in here

Auth, rate limiting, retries, metrics, structured logging, health probes, and graceful shutdown are all implemented in this file already — see the "Core SRE Features" section of the root [`README.md`](../README.md) for the current list and what each one does. This file won't re-list them; check there first so the two don't drift out of sync.
