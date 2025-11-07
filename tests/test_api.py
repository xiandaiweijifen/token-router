from fastapi.testclient import TestClient
import pytest

from app import routes
from app.main import app, allocator_dependency
from app.token_allocator import TokenAllocator


@pytest.fixture()
def client() -> TestClient:
    allocator = TokenAllocator(node_count=2, node_quota=100)
    app.dependency_overrides[routes.get_allocator] = lambda: allocator

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides[routes.get_allocator] = allocator_dependency


def test_alloc_success(client: TestClient) -> None:
    response = client.post(
        "/alloc",
        json={"request_id": "req-1", "token_count": 60},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["node_id"] in (0, 1)
    assert data["remaining_quota"] == 40


def test_alloc_overloaded(client: TestClient) -> None:
    client.post("/alloc", json={"request_id": "req-1", "token_count": 100})
    client.post("/alloc", json={"request_id": "req-2", "token_count": 100})

    response = client.post("/alloc", json={"request_id": "req-3", "token_count": 10})
    assert response.status_code == 429
    assert response.json()["detail"] == "overloaded"


def test_free_success(client: TestClient) -> None:
    client.post("/alloc", json={"request_id": "req-1", "token_count": 20})

    response = client.post("/free", json={"request_id": "req-1"})
    assert response.status_code == 200
    assert "node_id" in response.json()


def test_free_not_found(client: TestClient) -> None:
    response = client.post("/free", json={"request_id": "missing"})
    assert response.status_code == 404
    assert response.json()["detail"] == "not_found"
