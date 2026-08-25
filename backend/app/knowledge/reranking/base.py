from abc import ABC, abstractmethod

from app.knowledge.retrieval.models import RetrievalResult


class Reranker(ABC):
    @abstractmethod
    async def rerank(
        self, query: str, documents: list[RetrievalResult], top_k: int
    ) -> list[RetrievalResult]: ...
