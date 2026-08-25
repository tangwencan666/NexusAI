import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievalResult:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    metadata: dict[str, Any]
    source: dict[str, Any]
    score: float
    rank: int
    retrieval_method: str
    vector_score: float | None = None
    lexical_score: float | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None
    ranks: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalTrace:
    original_query: str
    rewritten_query: str
    vector_results: list[RetrievalResult] = field(default_factory=list)
    bm25_results: list[RetrievalResult] = field(default_factory=list)
    rrf_results: list[RetrievalResult] = field(default_factory=list)
    reranked_results: list[RetrievalResult] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)
