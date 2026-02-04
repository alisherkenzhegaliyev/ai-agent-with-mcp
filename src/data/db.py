# src/database/db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import os

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    in_stock = Column(Boolean, default=True)


# Ensure data directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__))
os.makedirs(DATA_DIR, exist_ok=True)

# Database connection with proper settings for concurrent writes
DATABASE_PATH = os.path.join(DATA_DIR, "products.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multi-threading
        "timeout": 30  # Wait up to 30 seconds for locks
    },
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Allow 20 extra connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Must be False for MCP stdio to work
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_db():
    """Context manager for database sessions with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit on success
    except Exception:
        db.rollback()  # Auto-rollback on error
        raise
    finally:
        db.close()  # Always close
