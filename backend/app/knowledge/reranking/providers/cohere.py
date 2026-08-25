import httpx

from app.core.exceptions import ApplicationError
from app.knowledge.reranking.base import Reranker
from app.knowledge.retrieval.models import RetrievalResult


class CohereReranker(Reranker):
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def rerank(self, query: str, documents: list[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        if not self.api_key:
            raise ApplicationError("RERANKER_UNAVAILABLE", "COHERE_API_KEY is not configured", 503)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.cohere.com/v2/rerank",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "query": query, "documents": [d.content for d in documents], "top_n": top_k},
                )
                response.raise_for_status()
            ranked = []
            for rank, item in enumerate(response.json()["results"], 1):
                document = documents[item["index"]]
                document.rerank_score = float(item["relevance_score"])
                document.score = document.rerank_score
                document.rank = rank
                document.retrieval_method = "rerank"
                ranked.append(document)
            return ranked
        except ApplicationError:
            raise
        except Exception as exc:
            raise ApplicationError("RERANKER_UNAVAILABLE", "Cohere rerank request failed", 502) from exc
