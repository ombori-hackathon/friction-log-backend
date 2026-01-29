"""
Database configuration and session management for Friction Log.

Uses SQLite for local storage with SQLAlchemy ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database URL
# Database file will be created in the project root
SQLALCHEMY_DATABASE_URL = "sqlite:///./friction_log.db"

# Create engine
# connect_args={"check_same_thread": False} is needed only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(FrictionItem).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database.

    Creates all tables defined in models.
    Safe to call multiple times - only creates tables that don't exist.
    """
    # Import models here to ensure they are registered with Base
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
