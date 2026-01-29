"""
Analytics calculations for friction items.

This module provides functions for calculating friction scores,
trends, and category breakdowns.
"""

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FrictionItem


def calculate_current_score(db: Session) -> dict:
    """
    Calculate the current friction score including encounter stats.

    The score is the sum of annoyance_level for all active items
    (status != 'fixed').

    Args:
        db: Database session

    Returns:
        dict: Current score, active item count, and encounter stats
    """
    # Query for active items (not fixed)
    active_items = db.query(FrictionItem).filter(FrictionItem.status != "fixed").all()

    # Calculate total score
    current_score = sum(item.annoyance_level for item in active_items)
    active_count = len(active_items)

    # Calculate encounter stats
    today = date.today()
    items_over_limit = 0
    total_encounters_today = 0

    for item in active_items:
        # Count today's encounters
        if item.last_encounter_date == today:
            total_encounters_today += item.encounter_count or 0

        # Check if item exceeded its limit
        if (
            item.encounter_limit is not None
            and item.last_encounter_date == today
            and item.encounter_count >= item.encounter_limit
        ):
            items_over_limit += 1

    return {
        "current_score": current_score,
        "active_count": active_count,
        "items_over_limit": items_over_limit,
        "total_encounters_today": total_encounters_today,
    }


def calculate_trend(db: Session, days: int = 30) -> list[dict]:
    """
    Calculate friction score trend over time.

    For each day in the specified period, calculates the friction score
    that would have been active on that day.

    Args:
        db: Database session
        days: Number of days to include in trend (default: 30)

    Returns:
        list[TrendDataPoint]: Daily scores sorted by date ascending
    """
    # Generate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    trend_data = []

    # Calculate score for each day
    for single_date in (start_date + timedelta(n) for n in range(days)):
        # Items active on this date:
        # - created_at <= single_date
        # - AND (fixed_at is NULL OR fixed_at > single_date)

        # Query items that existed and were not fixed on this date
        query = db.query(FrictionItem).filter(
            func.date(FrictionItem.created_at) <= single_date
        )

        # Filter out items that were fixed before this date
        query = query.filter(
            (FrictionItem.fixed_at.is_(None))
            | (func.date(FrictionItem.fixed_at) > single_date)
        )

        items = query.all()

        # Calculate score for this day
        daily_score = sum(item.annoyance_level for item in items)

        trend_data.append({"date": single_date.isoformat(), "score": daily_score})

    return trend_data


def calculate_category_breakdown(db: Session) -> dict:
    """
    Calculate friction score breakdown by category.

    Only includes active items (status != 'fixed').

    Args:
        db: Database session

    Returns:
        CategoryBreakdown: Scores by category (home, work, digital, health, other)
    """
    # Initialize all categories to 0
    breakdown = {
        "home": 0,
        "work": 0,
        "digital": 0,
        "health": 0,
        "other": 0,
    }

    # Query active items grouped by category
    active_items = db.query(FrictionItem).filter(FrictionItem.status != "fixed").all()

    # Sum annoyance levels by category
    for item in active_items:
        if item.category in breakdown:
            breakdown[item.category] += item.annoyance_level

    return breakdown
