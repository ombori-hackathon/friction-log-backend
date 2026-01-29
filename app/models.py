"""
SQLAlchemy database models for Friction Log.

Note: These are ORM models for database operations.
Pydantic models from the API contract are used for request/response validation.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String

from app.database import Base


class FrictionItem(Base):
    """
    SQLAlchemy model for friction items.

    Represents a single friction point that the user wants to track and eliminate.
    """

    __tablename__ = "friction_items"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Core fields
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)

    # Annoyance level: 1-5
    annoyance_level = Column(
        Integer,
        nullable=False,
        info={"check": "annoyance_level >= 1 AND annoyance_level <= 5"},
    )

    # Category: home, work, digital, health, other
    category = Column(String(50), nullable=False, index=True)

    # Status: not_fixed, in_progress, fixed
    status = Column(String(50), nullable=False, default="not_fixed", index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    fixed_at = Column(DateTime, nullable=True)

    # Add check constraint for annoyance_level
    __table_args__ = (
        CheckConstraint(
            "annoyance_level >= 1 AND annoyance_level <= 5",
            name="check_annoyance_level",
        ),
    )

    def __repr__(self):
        return (
            f"<FrictionItem(id={self.id}, "
            f"title='{self.title}', status='{self.status}')>"
        )
