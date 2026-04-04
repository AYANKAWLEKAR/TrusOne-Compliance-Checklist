import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


@pytest.mark.integration
def test_regulation_retrieval_tables_exist(db_session) -> None:
    try:
        tables = db_session.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename IN "
                "('regulations', 'regulation_vectors', 'source_documents', "
                "'source_document_chunks', 'regulation_document_links')"
            )
        ).scalars().all()
    except OperationalError as exc:  # pragma: no cover
        pytest.skip(f"Database not available: {exc}")

    assert set(tables) == {
        "regulations",
        "regulation_vectors",
        "source_documents",
        "source_document_chunks",
        "regulation_document_links",
    }
