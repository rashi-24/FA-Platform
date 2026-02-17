"""
Database configuration and session management
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

from models import Base

# Database configuration
# SECURITY: DATABASE_URL must be set in environment variables
# No default value for security - fails fast if not configured
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Example: postgresql://user:password@localhost:5432/dbname or sqlite:///./financial_advisor.db"
    )

# Create engine
# PostgreSQL (production)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # Set to True for SQL query logging
)

# For SQLite (development)
# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False},
#     poolclass=StaticPool,
#     echo=False
# )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database - create all tables
    Run this once during setup
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization complete!")


def drop_db():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped!")


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    Ensures proper session cleanup

    Usage:
        with get_db() as db:
            client = db.query(Client).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_db_session():
    """
    Dependency for FastAPI endpoints

    Usage in FastAPI:
        @app.get("/clients")
        def get_clients(db: Session = Depends(get_db_session)):
            return db.query(Client).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Transaction helper
class DatabaseTransaction:
    """
    Safe transaction wrapper with automatic rollback on error

    Usage:
        with DatabaseTransaction(db) as txn:
            txn.add(new_client)
            txn.add(new_policy)
            # Commits automatically if no exception
    """

    def __init__(self, db: Session):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
            return False
        else:
            self.db.commit()
            return True


if __name__ == "__main__":
    """
    Run this file directly to initialize the database:
    python database.py
    """
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_db()
    elif len(sys.argv) > 1 and sys.argv[1] == "drop":
        confirm = input("Are you sure you want to drop all tables? (yes/no): ")
        if confirm.lower() == "yes":
            drop_db()
    else:
        logger.info("Usage:")
        logger.info("  python database.py init  - Create all tables")
        logger.info("  python database.py drop  - Drop all tables (requires confirmation)")
