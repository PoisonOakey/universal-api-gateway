from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
async def test_health_probes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/healthz")
        assert res.status_code == 200
        res = await ac.get("/readyz")
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_metrics_exposed():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/metrics")
        assert res.status_code == 200
        assert "gateway_requests_total" in res.text

@pytest.mark.asyncio
async def test_proxy_unauthorized():
    with patch("src.main.API_AUTH_TOKEN", "test-token"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/weather/weather/current")
            assert res.status_code == 401

@pytest.mark.asyncio
async def test_proxy_success():
    import httpx
    app.state.client = httpx.AsyncClient()
    with patch("src.main.API_AUTH_TOKEN", "test-token"):
        with patch.object(app.state.client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value.status_code = 200
            mock_request.return_value.content = b'{"success": true}'
            mock_request.return_value.headers = {}

            async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 12345)), base_url="http://test") as ac:
                res = await ac.get("/api/weather/weather/current", headers={"Authorization": "Bearer test-token"})
                assert res.status_code == 200

@pytest.mark.asyncio
async def test_caller_credentials_not_forwarded_upstream():
    """The gateway's bearer token authenticates the caller to us, not to the upstream API."""
    import httpx
    app.state.client = httpx.AsyncClient()
    with patch("src.main.API_AUTH_TOKEN", "test-token"):
        with patch.object(app.state.client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value.status_code = 200
            mock_request.return_value.content = b'{"success": true}'
            mock_request.return_value.headers = {}

            async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 12345)), base_url="http://test") as ac:
                await ac.get(
                    "/api/weather/weather/current",
                    headers={"Authorization": "Bearer test-token", "Cookie": "session=secret"},
                )

            forwarded = {k.lower() for k in mock_request.call_args.kwargs["headers"]}
            assert "authorization" not in forwarded
            assert "cookie" not in forwarded


@pytest.mark.asyncio
async def test_rate_limiting():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Hit healthz 101 times to prove it's NOT rate limited
        for _ in range(101):
            res = await ac.get("/healthz")
            assert res.status_code == 200

        # Now hit proxy route >100 times to prove it IS rate limited
        import httpx
        app.state.client = httpx.AsyncClient()
        with patch("src.main.API_AUTH_TOKEN", "test-token"):
            with patch.object(app.state.client, "request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value.status_code = 200
                mock_request.return_value.content = b'{"success": true}'
                mock_request.return_value.headers = {}

                for _ in range(105):
                    res = await ac.get("/api/dummy/products", headers={"Authorization": "Bearer test-token"})
                    if res.status_code == 429:
                        break
                assert res.status_code == 429
