from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio

from app import routes
from app.main import app, allocator_dependency
from app.token_allocator import TokenAllocator


@pytest_asyncio.fixture()
async def client() -> AsyncClient:
    allocator = TokenAllocator(node_count=2, node_quota=100)
    app.dependency_overrides[routes.get_allocator] = lambda: allocator

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides[routes.get_allocator] = allocator_dependency


@pytest.mark.asyncio
async def test_alloc_success(client: AsyncClient) -> None:
    response = await client.post(
        "/alloc",
        json={"request_id": "req-1", "token_count": 60},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["node_id"] in (0, 1)
    assert data["remaining_quota"] == 40


@pytest.mark.asyncio
async def test_alloc_overloaded(client: AsyncClient) -> None:
    await client.post("/alloc", json={"request_id": "req-1", "token_count": 100})
    await client.post("/alloc", json={"request_id": "req-2", "token_count": 100})

    response = await client.post("/alloc", json={"request_id": "req-3", "token_count": 10})
    assert response.status_code == 429
    assert response.json()["detail"] == "overloaded"


@pytest.mark.asyncio
async def test_free_success(client: AsyncClient) -> None:
    await client.post("/alloc", json={"request_id": "req-1", "token_count": 20})

    response = await client.post("/free", json={"request_id": "req-1"})
    assert response.status_code == 200
    assert "node_id" in response.json()


@pytest.mark.asyncio
async def test_free_not_found(client: AsyncClient) -> None:
    response = await client.post("/free", json={"request_id": "missing"})
    assert response.status_code == 404
    assert response.json()["detail"] == "not_found"
