"""
CRUD operations for friction items.

This module provides database operations for creating, reading, updating,
and deleting friction items.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

# Import SQLAlchemy model
from app.models import FrictionItem

# Import generated Pydantic models from API contract
from contract.generated.python.models import (
    Category,
    FrictionItemCreate,
    FrictionItemResponse,
    FrictionItemUpdate,
    Status,
)


def friction_item_to_response(db_item: FrictionItem) -> FrictionItemResponse:
    """
    Convert SQLAlchemy FrictionItem to Pydantic FrictionItemResponse.

    Args:
        db_item: SQLAlchemy FrictionItem instance

    Returns:
        FrictionItemResponse: Pydantic model for API response
    """

    # Ensure datetimes have timezone info (SQLite strips it)
    def ensure_tz(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    return FrictionItemResponse(
        id=db_item.id,
        title=db_item.title,
        description=db_item.description,
        annoyance_level=db_item.annoyance_level,
        category=Category(db_item.category),
        status=Status(db_item.status),
        created_at=ensure_tz(db_item.created_at),
        updated_at=ensure_tz(db_item.updated_at),
        fixed_at=ensure_tz(db_item.fixed_at),
    )


def create_friction_item(db: Session, item: FrictionItemCreate) -> FrictionItemResponse:
    """
    Create a new friction item.

    Args:
        db: Database session
        item: FrictionItemCreate schema from API contract

    Returns:
        FrictionItemResponse: Created friction item
    """
    db_item = FrictionItem(
        title=item.title,
        description=item.description,
        annoyance_level=item.annoyance_level,
        category=item.category.value,
        status="not_fixed",  # Default status
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return friction_item_to_response(db_item)


def get_friction_items(
    db: Session,
    status: Optional[Status] = None,
    category: Optional[Category] = None,
) -> list[FrictionItemResponse]:
    """
    Get all friction items with optional filtering.

    Args:
        db: Database session
        status: Optional filter by status
        category: Optional filter by category

    Returns:
        list[FrictionItemResponse]: List of friction items
    """
    query = db.query(FrictionItem)

    # Apply filters if provided
    if status:
        query = query.filter(FrictionItem.status == status.value)
    if category:
        query = query.filter(FrictionItem.category == category.value)

    # Order by created_at descending (newest first)
    query = query.order_by(FrictionItem.created_at.desc())

    db_items = query.all()
    return [friction_item_to_response(item) for item in db_items]


def get_friction_item_by_id(
    db: Session, item_id: int
) -> Optional[FrictionItemResponse]:
    """
    Get a single friction item by ID.

    Args:
        db: Database session
        item_id: Friction item ID

    Returns:
        FrictionItemResponse if found, None otherwise
    """
    db_item = db.query(FrictionItem).filter(FrictionItem.id == item_id).first()

    if db_item is None:
        return None

    return friction_item_to_response(db_item)


def update_friction_item(
    db: Session, item_id: int, item_update: FrictionItemUpdate
) -> Optional[FrictionItemResponse]:
    """
    Update an existing friction item.

    Args:
        db: Database session
        item_id: Friction item ID
        item_update: FrictionItemUpdate schema with fields to update

    Returns:
        FrictionItemResponse if found and updated, None if not found

    Special logic:
        - If status changes to 'fixed', sets fixed_at timestamp
        - If status changes away from 'fixed', clears fixed_at timestamp
    """
    db_item = db.query(FrictionItem).filter(FrictionItem.id == item_id).first()

    if db_item is None:
        return None

    # Track old status for fixed_at logic
    old_status = db_item.status

    # Update fields that are provided (not None)
    update_data = item_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            # Convert enums to string values for database
            if isinstance(value, (Category, Status)):
                value = value.value
            setattr(db_item, field, value)

    # Handle fixed_at timestamp
    new_status = db_item.status
    if old_status != "fixed" and new_status == "fixed":
        # Status changed to fixed
        db_item.fixed_at = datetime.now(timezone.utc)
    elif old_status == "fixed" and new_status != "fixed":
        # Status changed away from fixed
        db_item.fixed_at = None

    db.commit()
    db.refresh(db_item)

    return friction_item_to_response(db_item)


def delete_friction_item(db: Session, item_id: int) -> bool:
    """
    Delete a friction item.

    Args:
        db: Database session
        item_id: Friction item ID

    Returns:
        bool: True if deleted, False if not found
    """
    db_item = db.query(FrictionItem).filter(FrictionItem.id == item_id).first()

    if db_item is None:
        return False

    db.delete(db_item)
    db.commit()

    return True
