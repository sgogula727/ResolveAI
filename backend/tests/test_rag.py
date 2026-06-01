import pytest

from backend.rag import (
    MistralEmbeddingClient,
    _chunk_text,
    _cosine_similarity,
    _normalize_embedding,
    search_chunks,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


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


@pytest.mark.asyncio
async def test_search_chunks_without_stored_chunks_skips_embedding(monkeypatch) -> None:
    class FakeScalars:
        def all(self) -> list:
            return []

    class FakeResult:
        def scalars(self) -> FakeScalars:
            return FakeScalars()

    class FakeSession:
        async def execute(self, statement) -> FakeResult:
            return FakeResult()

    def fail_embedder():
        raise AssertionError("Embedder should not be created when no chunks exist")

    monkeypatch.setattr("backend.rag._embedder", fail_embedder)

    assert await search_chunks(FakeSession(), "printer is offline") == []


@pytest.mark.asyncio
async def test_mistral_embedding_client_uses_embeddings_endpoint(monkeypatch) -> None:
    calls = []

    class FakeAsyncClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, url: str, json: dict, headers: dict) -> FakeResponse:
            calls.append({"url": url, "json": json, "headers": headers})
            return FakeResponse({"data": [{"embedding": [1.0, 0.0]}]})

    monkeypatch.setattr("backend.rag.httpx.AsyncClient", FakeAsyncClient)

    client = MistralEmbeddingClient(
        api_key="test-key",
        base_url="https://api.mistral.ai/v1/",
        model_name="mistral-embed",
    )
    result = await client.embed_query("printer is offline")

    assert result == [1.0, 0.0]
    assert calls[0]["url"] == "https://api.mistral.ai/v1/embeddings"
    assert calls[0]["json"] == {
        "input": ["printer is offline"],
        "model": "mistral-embed",
    }
