"""
API endpoint tests for Friction Log backend.

Tests the health check and root endpoints.
"""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Test the health check endpoint.

    Args:
        client: FastAPI test client fixture

    Verifies:
        - Response status code is 200
        - Response contains {"status": "ok"}
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client: TestClient):
    """
    Test the root endpoint.

    Args:
        client: FastAPI test client fixture

    Verifies:
        - Response status code is 200
        - Response contains API information
    """
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "Friction Log API"
    assert data["version"] == "1.0.0"


def test_api_docs_available(client: TestClient):
    """
    Test that API documentation is available.

    Args:
        client: FastAPI test client fixture

    Verifies:
        - /docs endpoint is accessible
        - /redoc endpoint is accessible
    """
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200
