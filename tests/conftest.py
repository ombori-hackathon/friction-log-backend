"""
Pytest configuration and fixtures for Friction Log backend tests.

This module provides reusable fixtures for testing the API.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Use in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_friction_log.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Create a fresh database for each test.

    Yields:
        Session: Database session for testing

    The database is created before the test and dropped after.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Create a test client with a test database.

    Args:
        db: Database session fixture

    Yields:
        TestClient: FastAPI test client

    This fixture overrides the get_db dependency to use the test database.
    """

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
