import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to School Coffee System API"}

@pytest.mark.asyncio
async def test_read_menu(client: AsyncClient):
    response = await client.get("/api/v1/menu/")
    # It might be empty initially, but should verify 200 OK
    assert response.status_code == 200
    assert isinstance(response.json(), list)
