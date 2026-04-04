import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


@pytest.mark.integration
def test_database_connection_and_pgvector_extension(db_session) -> None:
    try:
        value = db_session.execute(text("SELECT 1")).scalar_one()
        extension_present = db_session.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        ).scalar_one()
    except OperationalError as exc:  # pragma: no cover
        pytest.skip(f"Database not available: {exc}")

    assert value == 1
    assert extension_present is True
