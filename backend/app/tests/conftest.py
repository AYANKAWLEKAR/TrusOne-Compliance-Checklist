from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.session import connect_args_for_database_url


@pytest.fixture(scope="session")
def database_url() -> str:
    return settings.database_url


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        settings.database_url,
        future=True,
        connect_args=connect_args_for_database_url(settings.database_url),
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
