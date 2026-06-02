import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Solo ejecutar si hay base de datos disponible
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Definir RUN_INTEGRATION_TESTS=1 con Docker levantado",
)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    from app.main import app
    from app.core.database import lifespan

    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_admin_central(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin.central@sga.local",
            "password": "AdminCentral123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["rol"] == "ADMIN_CENTRAL"
