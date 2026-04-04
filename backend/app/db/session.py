from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


def connect_args_for_database_url(url: str) -> dict:
    # Supabase transaction pooler (port 6543) does not support server-side prepared statements.
    if ":6543" in url:
        return {"prepare_threshold": None}
    return {}


engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args_for_database_url(settings.database_url),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
