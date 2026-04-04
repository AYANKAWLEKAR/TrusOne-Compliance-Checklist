import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


@pytest.mark.integration
def test_vector_indexes_exist(db_session) -> None:
    try:
        indexes = db_session.execute(
            text(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname IN "
                "('ix_regulation_vectors_embedding_hnsw', 'ix_source_document_chunks_embedding_hnsw')"
            )
        ).scalars().all()
    except OperationalError as exc:  # pragma: no cover
        pytest.skip(f"Database not available: {exc}")

    assert set(indexes) == {
        "ix_regulation_vectors_embedding_hnsw",
        "ix_source_document_chunks_embedding_hnsw",
    }
