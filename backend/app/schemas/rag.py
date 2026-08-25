from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    conversation_id: UUID | None = None
    recent_messages: list[str] = Field(default_factory=list, max_length=10)


class CitationRead(BaseModel):
    id: int
    document_id: UUID
    chunk_id: UUID
    source_type: str | None
    title: str | None
    filename: str | None
    page: int | None
    url: str | None
    domain: str | None


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationRead]
    retrieval: dict[str, Any]
    trace: dict[str, Any]


class RetrievalDebugRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    mode: Literal["vector", "bm25", "hybrid", "rerank"] = "hybrid"
    top_k: int = Field(default=5, ge=1, le=50)


class RetrievalResultRead(BaseModel):
    chunk_id: UUID
    document_id: UUID
    content: str
    metadata: dict[str, Any]
    source: dict[str, Any]
    score: float
    rank: int
    retrieval_method: str
    vector_score: float | None
    lexical_score: float | None
    rrf_score: float | None
    rerank_score: float | None
    ranks: dict[str, int]


class RetrievalDebugResponse(BaseModel):
    original_query: str
    rewritten_query: str
    vector_results: list[RetrievalResultRead]
    bm25_results: list[RetrievalResultRead]
    rrf_results: list[RetrievalResultRead]
    reranked_results: list[RetrievalResultRead]
    timings_ms: dict[str, float]
