import asyncio
import time
import uuid

from app.core.config import settings
from app.knowledge.retrieval.base import Retriever
from app.knowledge.retrieval.models import RetrievalTrace
from app.knowledge.retrieval.rrf import reciprocal_rank_fusion


class HybridRetriever:
    def __init__(self, vector: Retriever, bm25: Retriever) -> None:
        self.vector = vector
        self.bm25 = bm25

    async def search(self, knowledge_base_id: uuid.UUID, query: str) -> RetrievalTrace:
        started = time.perf_counter()
        async def timed_search(retriever: Retriever, top_k: int):
            search_started = time.perf_counter()
            results = await retriever.search(knowledge_base_id, query, top_k)
            return results, (time.perf_counter() - search_started) * 1000

        vector_task = asyncio.create_task(timed_search(self.vector, settings.vector_top_k))
        bm25_task = asyncio.create_task(timed_search(self.bm25, settings.bm25_top_k))
        (vector_results, vector_ms), (bm25_results, bm25_ms) = await asyncio.gather(
            vector_task, bm25_task
        )
        retrieved = time.perf_counter()
        rrf_results = reciprocal_rank_fusion(
            [vector_results, bm25_results], settings.rrf_k, settings.hybrid_top_k
        )
        finished = time.perf_counter()
        return RetrievalTrace(
            original_query=query,
            rewritten_query=query,
            vector_results=vector_results,
            bm25_results=bm25_results,
            rrf_results=rrf_results,
            timings_ms={
                "vector": vector_ms,
                "bm25": bm25_ms,
                "vector_and_bm25": (retrieved - started) * 1000,
                "rrf": (finished - retrieved) * 1000,
                "total_retrieval": (finished - started) * 1000,
            },
        )
