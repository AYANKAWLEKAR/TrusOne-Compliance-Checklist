from app.ingestion.chunking import chunk_text, clean_text


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("a   b\nc") == "a b c"


def test_chunk_text_returns_chunks() -> None:
    text = "word " * 1200
    chunks = chunk_text(text, target_tokens=200, overlap_tokens=50)

    assert len(chunks) > 1
    assert all(chunk for chunk, _token_count in chunks)
