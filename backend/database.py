"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os

from models import Base

# Database configuration
# Using SQLite for development (no PostgreSQL setup required)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_advisor.db")

# For production with PostgreSQL, set DATABASE_URL environment variable:
# postgresql://advisor:advisor_pass@localhost:5432/financial_advisor

# Create engine
# SQLite for development
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # Set to True for SQL query logging
)

# For PostgreSQL (production)
# engine = create_engine(
#     DATABASE_URL,
#     pool_pre_ping=True,
#     echo=False
# )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database - create all tables
    Run this once during setup
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialization complete!")


def drop_db():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing
    """
    print("WARNING: Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")


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
            print(f"Transaction rolled back due to: {exc_val}")
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
        print("Usage:")
        print("  python database.py init  - Create all tables")
        print("  python database.py drop  - Drop all tables (requires confirmation)")
