from __future__ import annotations

import httpx
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import Document, DocumentChunk


def _build_api_url(base_url: str, endpoint: str) -> str:
    return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"


def _chunk_text(text: str, chunk_size: int = 400, chunk_overlap: int = 50) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - chunk_overlap
    return chunks


def _normalize_embedding(embedding: Any) -> list[float]:
    if embedding is None:
        return []
    if isinstance(embedding, list):
        return embedding
    if isinstance(embedding, tuple):
        return list(embedding)
    if hasattr(embedding, "tolist"):
        return list(embedding.tolist())
    return list(embedding)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _normalize_embedding_model_name(model_name: str) -> str:
    if model_name == "mistral-7b-embeddings":
        return "mistral-embed"
    return model_name


class MistralEmbeddingClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or settings.mistral_api_key
        self.base_url = base_url or settings.mistral_api_base_url
        self.model_name = _normalize_embedding_model_name(
            model_name or settings.mistral_embedding_model
        )
        self.timeout = timeout

        if not self.api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is required to use the Mistral embeddings client."
            )

    async def embed_query(self, query: str) -> list[float]:
        embeddings = await self._embed([query])
        return embeddings[0] if embeddings else []

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts)

    async def _embed(self, inputs: list[str]) -> list[list[float]]:
        url = _build_api_url(self.base_url, "embeddings")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"input": inputs, "model": self.model_name}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = data.get("data", [])
        return [item.get("embedding", []) for item in results]


def _embedder() -> MistralEmbeddingClient:
    return MistralEmbeddingClient()


async def create_document(
    session: AsyncSession,
    title: str,
    source: str,
    content: str,
    metadata: dict[str, Any] | None = None,
    chunk_size: int = 400,
    chunk_overlap: int = 50,
) -> Document:
    document = Document(title=title, source=source, content=content, doc_metadata=metadata)
    session.add(document)
    await session.flush()

    chunks = []
    text_chunks = _chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    embeddings = await _embedder().embed_documents(text_chunks)

    for chunk_text, embedding in zip(text_chunks, embeddings):
        chunks.append(
            DocumentChunk(
                document_id=document.id,
                chunk_text=chunk_text,
                embedding=embedding,
            )
        )

    session.add_all(chunks)
    await session.commit()
    await session.refresh(document)
    return document


async def get_document_chunks(session: AsyncSession, document_id: int) -> list[DocumentChunk]:
    result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    return result.scalars().all()


async def search_chunks(
    session: AsyncSession,
    query: str,
    top_k: int = 3,
) -> list[DocumentChunk]:
    if not query:
        return []

    result = await session.execute(select(DocumentChunk).order_by(DocumentChunk.id))
    chunks = result.scalars().all()
    if not chunks:
        return []

    query_embedding = await _embedder().embed_query(query)
    scored_chunks: list[tuple[float, DocumentChunk]] = []
    for chunk in chunks:
        chunk_embedding = _normalize_embedding(chunk.embedding)
        score = _cosine_similarity(query_embedding, chunk_embedding)
        scored_chunks.append((score, chunk))

    top_chunks = [chunk for score, chunk in sorted(scored_chunks, key=lambda item: item[0], reverse=True)[:top_k]]
    return top_chunks


async def build_context(session: AsyncSession, query: str, top_k: int = 3) -> str:
    chunks = await search_chunks(session, query, top_k=top_k)
    if not chunks:
        return "No relevant documents found in the knowledge base."
    return "\n\n".join(
        f"Source: {chunk.document.title if chunk.document else 'unknown'}\n{chunk.chunk_text}" for chunk in chunks
    )
