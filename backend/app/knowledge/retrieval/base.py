import uuid
from abc import ABC, abstractmethod

from app.knowledge.retrieval.models import RetrievalResult


class Retriever(ABC):
    @abstractmethod
    async def search(
        self, knowledge_base_id: uuid.UUID, query: str, top_k: int
    ) -> list[RetrievalResult]: ...
