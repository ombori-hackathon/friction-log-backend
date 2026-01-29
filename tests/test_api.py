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


# ==================== Friction Items CRUD Tests ====================


def test_create_friction_item(client: TestClient):
    """Test creating a new friction item."""
    payload = {
        "title": "Slow internet connection",
        "description": "WiFi is weak in home office",
        "annoyance_level": 4,
        "category": "digital",
    }

    response = client.post("/api/friction-items", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["annoyance_level"] == payload["annoyance_level"]
    assert data["category"] == payload["category"]
    assert data["status"] == "not_fixed"  # Default status
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["fixed_at"] is None


def test_create_friction_item_minimal(client: TestClient):
    """Test creating friction item with minimal required fields."""
    payload = {
        "title": "Kitchen cabinet squeaks",
        "annoyance_level": 2,
        "category": "home",
    }

    response = client.post("/api/friction-items", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] is None  # Optional field
    assert data["annoyance_level"] == payload["annoyance_level"]
    assert data["category"] == payload["category"]


def test_create_friction_item_validation_errors(client: TestClient):
    """Test validation errors when creating friction item."""
    # Missing required fields
    response = client.post("/api/friction-items", json={})
    assert response.status_code == 422

    # Invalid annoyance_level (too low)
    payload = {
        "title": "Test",
        "annoyance_level": 0,
        "category": "home",
    }
    response = client.post("/api/friction-items", json=payload)
    assert response.status_code == 422

    # Invalid annoyance_level (too high)
    payload["annoyance_level"] = 6
    response = client.post("/api/friction-items", json=payload)
    assert response.status_code == 422

    # Invalid category
    payload = {
        "title": "Test",
        "annoyance_level": 3,
        "category": "invalid_category",
    }
    response = client.post("/api/friction-items", json=payload)
    assert response.status_code == 422


def test_list_friction_items_empty(client: TestClient):
    """Test listing friction items when database is empty."""
    response = client.get("/api/friction-items")

    assert response.status_code == 200
    assert response.json() == []


def test_list_friction_items(client: TestClient):
    """Test listing all friction items."""
    # Create multiple items
    items = [
        {
            "title": "Item 1",
            "annoyance_level": 3,
            "category": "home",
        },
        {
            "title": "Item 2",
            "annoyance_level": 5,
            "category": "work",
        },
        {
            "title": "Item 3",
            "annoyance_level": 2,
            "category": "digital",
        },
    ]

    for item in items:
        client.post("/api/friction-items", json=item)

    # Get all items
    response = client.get("/api/friction-items")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Check they're ordered by created_at descending (newest first)
    assert data[0]["title"] == "Item 3"
    assert data[1]["title"] == "Item 2"
    assert data[2]["title"] == "Item 1"


def test_list_friction_items_filter_by_status(client: TestClient):
    """Test filtering friction items by status."""
    # Create items with different statuses
    client.post(
        "/api/friction-items",
        json={
            "title": "Not Fixed Item",
            "annoyance_level": 3,
            "category": "home",
        },
    )

    # Create and mark as in_progress
    response = client.post(
        "/api/friction-items",
        json={
            "title": "In Progress Item",
            "annoyance_level": 4,
            "category": "work",
        },
    )
    item_id = response.json()["id"]
    client.put(f"/api/friction-items/{item_id}", json={"status": "in_progress"})

    # Filter by not_fixed
    response = client.get("/api/friction-items?status=not_fixed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Not Fixed Item"

    # Filter by in_progress
    response = client.get("/api/friction-items?status=in_progress")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "In Progress Item"

    # Filter by fixed (should be empty)
    response = client.get("/api/friction-items?status=fixed")
    assert response.status_code == 200
    assert response.json() == []


def test_list_friction_items_filter_by_category(client: TestClient):
    """Test filtering friction items by category."""
    # Create items with different categories
    categories = ["home", "work", "digital"]
    for cat in categories:
        client.post(
            "/api/friction-items",
            json={
                "title": f"{cat.title()} Item",
                "annoyance_level": 3,
                "category": cat,
            },
        )

    # Filter by category
    for cat in categories:
        response = client.get(f"/api/friction-items?category={cat}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == cat


def test_get_friction_item_by_id(client: TestClient):
    """Test getting a single friction item by ID."""
    # Create item
    payload = {
        "title": "Test Item",
        "annoyance_level": 3,
        "category": "home",
    }
    create_response = client.post("/api/friction-items", json=payload)
    item_id = create_response.json()["id"]

    # Get item by ID
    response = client.get(f"/api/friction-items/{item_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["title"] == payload["title"]


def test_get_friction_item_not_found(client: TestClient):
    """Test getting a non-existent friction item returns 404."""
    response = client.get("/api/friction-items/9999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_friction_item(client: TestClient):
    """Test updating a friction item."""
    # Create item
    create_response = client.post(
        "/api/friction-items",
        json={
            "title": "Original Title",
            "annoyance_level": 3,
            "category": "home",
        },
    )
    item_id = create_response.json()["id"]

    # Update item
    update_payload = {
        "title": "Updated Title",
        "annoyance_level": 5,
    }
    response = client.put(f"/api/friction-items/{item_id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["title"] == "Updated Title"
    assert data["annoyance_level"] == 5
    assert data["category"] == "home"  # Unchanged


def test_update_friction_item_status_to_fixed(client: TestClient):
    """Test updating status to fixed sets fixed_at timestamp."""
    # Create item
    create_response = client.post(
        "/api/friction-items",
        json={
            "title": "Test Item",
            "annoyance_level": 3,
            "category": "home",
        },
    )
    item_id = create_response.json()["id"]

    # Update status to fixed
    response = client.put(f"/api/friction-items/{item_id}", json={"status": "fixed"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fixed"
    assert data["fixed_at"] is not None  # Timestamp should be set


def test_update_friction_item_status_from_fixed(client: TestClient):
    """Test updating status away from fixed clears fixed_at."""
    # Create and mark as fixed
    create_response = client.post(
        "/api/friction-items",
        json={
            "title": "Test Item",
            "annoyance_level": 3,
            "category": "home",
        },
    )
    item_id = create_response.json()["id"]
    client.put(f"/api/friction-items/{item_id}", json={"status": "fixed"})

    # Change status back to in_progress
    response = client.put(
        f"/api/friction-items/{item_id}", json={"status": "in_progress"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["fixed_at"] is None  # Timestamp should be cleared


def test_update_friction_item_not_found(client: TestClient):
    """Test updating a non-existent friction item returns 404."""
    response = client.put(
        "/api/friction-items/9999",
        json={"title": "Updated"},
    )

    assert response.status_code == 404


def test_delete_friction_item(client: TestClient):
    """Test deleting a friction item."""
    # Create item
    create_response = client.post(
        "/api/friction-items",
        json={
            "title": "To Delete",
            "annoyance_level": 3,
            "category": "home",
        },
    )
    item_id = create_response.json()["id"]

    # Delete item
    response = client.delete(f"/api/friction-items/{item_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/friction-items/{item_id}")
    assert get_response.status_code == 404


def test_delete_friction_item_not_found(client: TestClient):
    """Test deleting a non-existent friction item returns 404."""
    response = client.delete("/api/friction-items/9999")
    assert response.status_code == 404
