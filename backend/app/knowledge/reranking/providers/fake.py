import re
from dataclasses import replace

from app.knowledge.reranking.base import Reranker
from app.knowledge.retrieval.models import RetrievalResult


class FakeReranker(Reranker):
    async def rerank(self, query: str, documents: list[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        terms = set(re.findall(r"\w+", query.lower()))
        scored = []
        for document in documents:
            words = set(re.findall(r"\w+", document.content.lower()))
            overlap = len(terms & words) / max(1, len(terms))
            score = overlap + (document.rrf_score or document.score)
            scored.append(replace(document, rerank_score=score, score=score, retrieval_method="rerank"))
        scored.sort(key=lambda item: item.score, reverse=True)
        for rank, item in enumerate(scored[:top_k], 1):
            item.rank = rank
        return scored[:top_k]
