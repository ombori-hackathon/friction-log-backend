"""
Analytics endpoint tests for Friction Log backend.

Tests the analytics endpoints for score calculation, trends, and breakdowns.
"""

from fastapi.testclient import TestClient


def test_current_score_empty_database(client: TestClient):
    """Test current score with empty database."""
    response = client.get("/api/analytics/score")

    assert response.status_code == 200
    data = response.json()
    assert data["current_score"] == 0
    assert data["active_count"] == 0


def test_current_score_with_active_items(client: TestClient):
    """Test current score calculation with active items."""
    # Create friction items with different statuses
    items = [
        {"title": "Item 1", "annoyance_level": 3, "category": "home"},
        {"title": "Item 2", "annoyance_level": 5, "category": "work"},
        {"title": "Item 3", "annoyance_level": 2, "category": "digital"},
    ]

    for item in items:
        client.post("/api/friction-items", json=item)

    # Get current score
    response = client.get("/api/analytics/score")

    assert response.status_code == 200
    data = response.json()
    assert data["current_score"] == 10  # 3 + 5 + 2
    assert data["active_count"] == 3


def test_current_score_excludes_fixed_items(client: TestClient):
    """Test that current score excludes fixed items."""
    # Create items
    client.post(
        "/api/friction-items",
        json={"title": "Item 1", "annoyance_level": 3, "category": "home"},
    )
    response2 = client.post(
        "/api/friction-items",
        json={"title": "Item 2", "annoyance_level": 5, "category": "work"},
    )
    client.post(
        "/api/friction-items",
        json={"title": "Item 3", "annoyance_level": 2, "category": "digital"},
    )

    # Mark one as fixed
    item2_id = response2.json()["id"]
    client.put(f"/api/friction-items/{item2_id}", json={"status": "fixed"})

    # Get current score
    response = client.get("/api/analytics/score")

    assert response.status_code == 200
    data = response.json()
    assert data["current_score"] == 5  # 3 + 2 (excludes fixed item with 5)
    assert data["active_count"] == 2


def test_current_score_includes_in_progress(client: TestClient):
    """Test that current score includes in_progress items."""
    # Create item and mark as in_progress
    response = client.post(
        "/api/friction-items",
        json={"title": "Item", "annoyance_level": 4, "category": "home"},
    )
    item_id = response.json()["id"]
    client.put(f"/api/friction-items/{item_id}", json={"status": "in_progress"})

    # Get current score
    response = client.get("/api/analytics/score")

    assert response.status_code == 200
    data = response.json()
    assert data["current_score"] == 4
    assert data["active_count"] == 1


def test_trend_empty_database(client: TestClient):
    """Test trend with empty database."""
    response = client.get("/api/analytics/trend?days=7")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    # All scores should be 0
    for day in data:
        assert day["score"] == 0
        assert "date" in day


def test_trend_with_items(client: TestClient):
    """Test trend calculation with items."""
    # Create some items
    client.post(
        "/api/friction-items",
        json={"title": "Item 1", "annoyance_level": 3, "category": "home"},
    )
    client.post(
        "/api/friction-items",
        json={"title": "Item 2", "annoyance_level": 5, "category": "work"},
    )

    # Get trend for last 7 days
    response = client.get("/api/analytics/trend?days=7")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7

    # Last day should have score of 8 (3 + 5)
    assert data[-1]["score"] == 8


def test_trend_custom_days(client: TestClient):
    """Test trend with custom number of days."""
    # Create item
    client.post(
        "/api/friction-items",
        json={"title": "Item", "annoyance_level": 4, "category": "home"},
    )

    # Test different day ranges
    for days in [1, 7, 30, 90]:
        response = client.get(f"/api/analytics/trend?days={days}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == days


def test_trend_validation_errors(client: TestClient):
    """Test trend validation for invalid days parameter."""
    # days < 1
    response = client.get("/api/analytics/trend?days=0")
    assert response.status_code == 422

    # days > 365
    response = client.get("/api/analytics/trend?days=366")
    assert response.status_code == 422


def test_category_breakdown_empty_database(client: TestClient):
    """Test category breakdown with empty database."""
    response = client.get("/api/analytics/by-category")

    assert response.status_code == 200
    data = response.json()
    assert data["home"] == 0
    assert data["work"] == 0
    assert data["digital"] == 0
    assert data["health"] == 0
    assert data["other"] == 0


def test_category_breakdown_with_items(client: TestClient):
    """Test category breakdown calculation."""
    # Create items in different categories
    items = [
        {
            "title": "Home 1",
            "annoyance_level": 3,
            "category": "home",
        },
        {
            "title": "Home 2",
            "annoyance_level": 2,
            "category": "home",
        },
        {
            "title": "Work 1",
            "annoyance_level": 5,
            "category": "work",
        },
        {
            "title": "Digital 1",
            "annoyance_level": 4,
            "category": "digital",
        },
        {
            "title": "Health 1",
            "annoyance_level": 1,
            "category": "health",
        },
    ]

    for item in items:
        client.post("/api/friction-items", json=item)

    # Get category breakdown
    response = client.get("/api/analytics/by-category")

    assert response.status_code == 200
    data = response.json()
    assert data["home"] == 5  # 3 + 2
    assert data["work"] == 5
    assert data["digital"] == 4
    assert data["health"] == 1
    assert data["other"] == 0  # No items in this category


def test_category_breakdown_excludes_fixed(client: TestClient):
    """Test that category breakdown excludes fixed items."""
    # Create home items
    client.post(
        "/api/friction-items",
        json={"title": "Home 1", "annoyance_level": 3, "category": "home"},
    )
    response2 = client.post(
        "/api/friction-items",
        json={"title": "Home 2", "annoyance_level": 5, "category": "home"},
    )

    # Mark one as fixed
    item2_id = response2.json()["id"]
    client.put(f"/api/friction-items/{item2_id}", json={"status": "fixed"})

    # Get category breakdown
    response = client.get("/api/analytics/by-category")

    assert response.status_code == 200
    data = response.json()
    assert data["home"] == 3  # Only the unfixed item
    assert data["work"] == 0
    assert data["digital"] == 0
    assert data["health"] == 0
    assert data["other"] == 0


def test_category_breakdown_includes_in_progress(client: TestClient):
    """Test that category breakdown includes in_progress items."""
    # Create item and mark as in_progress
    response = client.post(
        "/api/friction-items",
        json={"title": "Item", "annoyance_level": 4, "category": "work"},
    )
    item_id = response.json()["id"]
    client.put(f"/api/friction-items/{item_id}", json={"status": "in_progress"})

    # Get category breakdown
    response = client.get("/api/analytics/by-category")

    assert response.status_code == 200
    data = response.json()
    assert data["work"] == 4  # in_progress items are included
    assert data["home"] == 0
