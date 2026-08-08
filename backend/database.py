"""SQLAlchemy database setup — SQLite for local/dev, easily swappable to PostgreSQL."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

# SQLite stored alongside the data directory (overridable via env)
_DB_PATH = Path("./lexaudit.db").resolve()
_DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(
    _DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI threads
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Called once on app startup."""
    from db_models import User, Subscription  # noqa: F401  (registers models)
    Base.metadata.create_all(bind=engine)
