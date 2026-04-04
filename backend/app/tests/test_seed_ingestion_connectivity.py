import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


@pytest.mark.integration
def test_documents_and_chunks_tables_exist(db_session) -> None:
    try:
        tables = db_session.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename IN ('documents', 'document_chunks')"
            )
        ).scalars().all()
    except OperationalError as exc:  # pragma: no cover
        pytest.skip(f"Database not available: {exc}")

    assert set(tables) == {"documents", "document_chunks"}
