import pytest

from backend.rag import _chunk_text, _cosine_similarity, _normalize_embedding


def test_chunk_text_splits_large_document() -> None:
    text = "word " * 1200
    chunks = _chunk_text(text, chunk_size=200, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk.split()) <= 200 for chunk in chunks)
    assert chunks[0].split()[:3] == ["word", "word", "word"]


def test_cosine_similarity_perfect_match() -> None:
    vector = [1.0, 0.0, 0.0]
    score = _cosine_similarity(vector, vector)

    assert score == pytest.approx(1.0)


def test_cosine_similarity_different_vectors() -> None:
    a = [1.0, 0.0]
    b = [0.0, 1.0]

    assert _cosine_similarity(a, b) == pytest.approx(0.0)


def test_normalize_embedding_empty() -> None:
    assert _normalize_embedding(None) == []
    assert _normalize_embedding((1.0, 2.0)) == [1.0, 2.0]
