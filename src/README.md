# Python Core Engine

This directory contains the beating heart of the Gateway: `main.py`.

> [!WARNING]
> **Do not edit `main.py` unless you are a backend developer.** 
> To add or modify API routes, you should edit `config/gateway.yaml` instead. The engine will automatically generate the routes for you.

---

## What does `main.py` actually do?

Unlike a traditional web application where every route (like `/weather` or `/stocks`) is hardcoded in Python, `main.py` is entirely dynamic.

When you run this file (via Docker or `start.bat`), it performs the following lifecycle:

1. **Initialization:** It spins up a high-performance ASGI web server using FastAPI and Uvicorn.
2. **Configuration Parse:** It reads the `config/gateway.yaml` file from the filesystem.
3. **Dynamic Generation:** For every API defined in the YAML, it uses `httpx` (an asynchronous HTTP client) to dynamically spawn a reverse-proxy route in FastAPI.
4. **Proxying:** When a request hits the Gateway, `main.py` intercepts it, parses any parameters, forwards the exact request to the external API, and seamlessly pipes the response back to the user.

## Why abstract it?

By forcing all configuration into a YAML file, we achieve true **Separation of Concerns**:
- **DevOps/Users** can manage API endpoints and keys without knowing Python.
- **Backend Developers** can upgrade the `main.py` engine (e.g., adding Redis caching, rate limiting, or global authentication) without breaking the user's API routes.
