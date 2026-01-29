"""
SQLAlchemy database models for Friction Log.

Note: These are ORM models for database operations.
Pydantic models from the API contract are used for request/response validation.
"""

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, Date, DateTime, Integer, String

from app.database import Base


def utc_now():
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


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
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    fixed_at = Column(DateTime, nullable=True)

    # Encounter tracking (daily resets)
    encounter_count = Column(Integer, nullable=False, default=0)
    encounter_limit = Column(Integer, nullable=True)  # Optional daily limit
    last_encounter_date = Column(Date, nullable=True)  # Date of last encounter

    # Add check constraints
    __table_args__ = (
        CheckConstraint(
            "annoyance_level >= 1 AND annoyance_level <= 5",
            name="check_annoyance_level",
        ),
        CheckConstraint("encounter_count >= 0", name="check_encounter_count_positive"),
        CheckConstraint(
            "encounter_limit IS NULL OR encounter_limit >= 1",
            name="check_encounter_limit_positive",
        ),
    )

    def __repr__(self):
        return (
            f"<FrictionItem(id={self.id}, "
            f"title='{self.title}', status='{self.status}')>"
        )
