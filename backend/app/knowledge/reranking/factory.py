from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.knowledge.reranking.base import Reranker
from app.knowledge.reranking.providers.cohere import CohereReranker
from app.knowledge.reranking.providers.fake import FakeReranker


def get_reranker() -> Reranker:
    if settings.reranker_provider == "fake":
        return FakeReranker()
    if settings.reranker_provider == "cohere":
        return CohereReranker(settings.cohere_api_key, settings.reranker_model)
    raise ApplicationError("RERANKER_UNAVAILABLE", f"Unknown reranker: {settings.reranker_provider}", 503)
