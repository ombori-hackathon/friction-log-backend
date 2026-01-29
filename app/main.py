"""
Main FastAPI application for Friction Log backend.

This module initializes the FastAPI app, configures CORS, and defines
the health check endpoint.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import analytics, crud
from app.database import get_db, init_db
from app.models import Settings
from contract.generated.python.models import (
    Category,
    FrictionItemCreate,
    FrictionItemUpdate,
    Status,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.

    Initializes database on startup.
    """
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: Add any cleanup code here if needed


# Create FastAPI app
app = FastAPI(
    title="Friction Log API",
    version="1.0.0",
    description=(
        "REST API for tracking daily life friction items and "
        "measuring progress in eliminating them."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for macOS app
# Allow requests from localhost during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (if ever used)
        "http://127.0.0.1:3000",
        "*",  # Allow all for local development
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status indicating the server is healthy

    Example:
        >>> GET /health
        {"status": "ok"}
    """
    return {"status": "ok"}


# Root endpoint
@app.get("/", tags=["health"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API name, version, and documentation link
    """
    return {
        "name": "Friction Log API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ==================== Friction Items CRUD Endpoints ====================


@app.post(
    "/api/friction-items",
    status_code=status.HTTP_201_CREATED,
    tags=["friction-items"],
)
async def create_friction_item(item: FrictionItemCreate, db: Session = Depends(get_db)):
    """
    Create a new friction item.

    Args:
        item: Friction item data (from request body)
        db: Database session (injected)

    Returns:
        FrictionItemResponse: Created friction item with ID and timestamps

    Raises:
        HTTPException: 422 if validation fails
    """
    return crud.create_friction_item(db, item)


@app.get(
    "/api/friction-items",
    tags=["friction-items"],
)
async def list_friction_items(
    status: Optional[Status] = None,
    category: Optional[Category] = None,
    db: Session = Depends(get_db),
):
    """
    List all friction items with optional filtering.

    Args:
        status: Optional filter by status (not_fixed, in_progress, fixed)
        category: Optional filter by category (home, work, digital, etc.)
        db: Database session (injected)

    Returns:
        list[FrictionItemResponse]: List of friction items (newest first)
    """
    return crud.get_friction_items(db, status=status, category=category)


@app.get(
    "/api/friction-items/{item_id}",
    tags=["friction-items"],
)
async def get_friction_item(item_id: int, db: Session = Depends(get_db)):
    """
    Get a single friction item by ID.

    Args:
        item_id: Friction item ID (from path parameter)
        db: Database session (injected)

    Returns:
        FrictionItemResponse: Friction item details

    Raises:
        HTTPException: 404 if item not found
    """
    db_item = crud.get_friction_item_by_id(db, item_id)

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friction item not found",
        )

    return db_item


@app.put(
    "/api/friction-items/{item_id}",
    tags=["friction-items"],
)
async def update_friction_item(
    item_id: int, item_update: FrictionItemUpdate, db: Session = Depends(get_db)
):
    """
    Update an existing friction item.

    Args:
        item_id: Friction item ID (from path parameter)
        item_update: Fields to update (from request body)
        db: Database session (injected)

    Returns:
        FrictionItemResponse: Updated friction item

    Raises:
        HTTPException: 404 if item not found
        HTTPException: 422 if validation fails

    Special behavior:
        - If status changes to 'fixed', sets fixed_at timestamp
        - If status changes away from 'fixed', clears fixed_at timestamp
    """
    db_item = crud.update_friction_item(db, item_id, item_update)

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friction item not found",
        )

    return db_item


@app.delete(
    "/api/friction-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["friction-items"],
)
async def delete_friction_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete a friction item by ID.

    Args:
        item_id: Friction item ID (from path parameter)
        db: Database session (injected)

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 404 if item not found
    """
    success = crud.delete_friction_item(db, item_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friction item not found",
        )

    return None


@app.post(
    "/api/friction-items/{item_id}/encounter",
    tags=["friction-items"],
)
async def increment_encounter(item_id: int, db: Session = Depends(get_db)):
    """
    Increment encounter count for a friction item.

    Resets counter to 1 if it's a new day since last encounter.
    Otherwise increments the existing count.

    Args:
        item_id: Friction item ID (from path parameter)
        db: Database session (injected)

    Returns:
        dict: Updated friction item with encounter count and is_limit_exceeded flag

    Raises:
        HTTPException: 404 if item not found
    """
    updated_item = crud.increment_encounter(db, item_id)

    if updated_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friction item not found",
        )

    return updated_item


# ==================== Analytics Endpoints ====================


@app.get(
    "/api/analytics/score",
    tags=["analytics"],
)
async def get_current_score(db: Session = Depends(get_db)):
    """
    Get the current friction score.

    Calculates the sum of annoyance_level for all active items
    (status != 'fixed').

    Args:
        db: Database session (injected)

    Returns:
        CurrentScore: Current friction score and active item count

    Example:
        >>> GET /api/analytics/score
        {"current_score": 23, "active_count": 7}
    """
    return analytics.calculate_current_score(db)


@app.get(
    "/api/analytics/trend",
    tags=["analytics"],
)
async def get_friction_trend(days: int = 30, db: Session = Depends(get_db)):
    """
    Get historical friction score trend.

    Returns daily friction scores for the specified time period.
    For each day, calculates what the friction score would have been
    based on items that existed and were not fixed on that day.

    Args:
        days: Number of days to include (default: 30, max: 365)
        db: Database session (injected)

    Returns:
        list[TrendDataPoint]: Daily scores sorted by date ascending

    Example:
        >>> GET /api/analytics/trend?days=7
        [
            {"date": "2026-01-23", "score": 28},
            {"date": "2026-01-24", "score": 26},
            ...
        ]
    """
    # Validate days parameter
    if days < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="days must be at least 1",
        )
    if days > 365:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="days must not exceed 365",
        )

    return analytics.calculate_trend(db, days=days)


@app.get(
    "/api/analytics/by-category",
    tags=["analytics"],
)
async def get_friction_by_category(db: Session = Depends(get_db)):
    """
    Get friction score breakdown by category.

    Returns the sum of annoyance_level for each category,
    only including active items (status != 'fixed').

    Args:
        db: Database session (injected)

    Returns:
        CategoryBreakdown: Scores by category

    Example:
        >>> GET /api/analytics/by-category
        {
            "home": 8,
            "work": 12,
            "digital": 5,
            "health": 3,
            "other": 0
        }
    """
    return analytics.calculate_category_breakdown(db)


# ==================== Settings Endpoints ====================


@app.get(
    "/api/settings/global-daily-limit",
    tags=["settings"],
)
async def get_global_daily_limit(db: Session = Depends(get_db)):
    """
    Get the global daily encounter limit.

    Returns the maximum number of total encounters allowed per day
    across all friction items.

    Args:
        db: Database session (injected)

    Returns:
        dict: Global daily limit (null if not set)

    Example:
        >>> GET /api/settings/global-daily-limit
        {"limit": 20}
    """
    setting = db.query(Settings).filter(Settings.key == "global_daily_limit").first()
    if setting is None:
        return {"limit": None}
    return {"limit": int(setting.value)}


@app.put(
    "/api/settings/global-daily-limit",
    tags=["settings"],
)
async def set_global_daily_limit(
    limit: Optional[int] = None, db: Session = Depends(get_db)
):
    """
    Set the global daily encounter limit.

    Args:
        limit: Maximum number of total encounters per day (null to disable)
        db: Database session (injected)

    Returns:
        dict: Updated global daily limit

    Raises:
        HTTPException: 422 if limit is less than 1

    Example:
        >>> PUT /api/settings/global-daily-limit?limit=20
        {"limit": 20}
    """
    if limit is not None and limit < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Global daily limit must be at least 1",
        )

    setting = db.query(Settings).filter(Settings.key == "global_daily_limit").first()

    if limit is None:
        # Remove the setting
        if setting:
            db.delete(setting)
            db.commit()
        return {"limit": None}

    if setting is None:
        # Create new setting
        setting = Settings(key="global_daily_limit", value=str(limit))
        db.add(setting)
    else:
        # Update existing setting
        setting.value = str(limit)

    db.commit()
    return {"limit": limit}
