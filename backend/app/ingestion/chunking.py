from __future__ import annotations

try:
    import tiktoken
except ImportError:  # pragma: no cover
    tiktoken = None


def clean_text(text: str) -> str:
    return " ".join(text.split())


def count_tokens(text: str) -> int:
    if tiktoken is None:
        return len(text.split())
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def chunk_text(text: str, target_tokens: int = 500, overlap_tokens: int = 100) -> list[tuple[str, int]]:
    words = clean_text(text).split()
    if not words:
        return []

    chunks: list[tuple[str, int]] = []
    step = max(target_tokens - overlap_tokens, 1)
    for start in range(0, len(words), step):
        slice_words = words[start : start + target_tokens]
        if not slice_words:
            continue
        chunk = " ".join(slice_words)
        chunks.append((chunk, count_tokens(chunk)))
        if start + target_tokens >= len(words):
            break
    return chunks
