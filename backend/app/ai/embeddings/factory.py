from app.ai.embeddings.base import EmbeddingProvider
from app.ai.embeddings.providers.fake import FakeEmbeddingProvider
from app.ai.embeddings.providers.openai import OpenAIEmbeddingProvider
from app.ai.embeddings.cache import CachedEmbeddingProvider
from app.core.config import settings
from app.core.exceptions import ApplicationError


def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        provider: EmbeddingProvider = OpenAIEmbeddingProvider(
            settings.openai_api_key, settings.embedding_model, settings.embedding_dimension
        )
    elif settings.embedding_provider == "fake":
        provider = FakeEmbeddingProvider(settings.embedding_dimension)
    else:
        raise ApplicationError(
            "EMBEDDING_PROVIDER_UNAVAILABLE",
            f"Unknown embedding provider: {settings.embedding_provider}",
            503,
        )
    return CachedEmbeddingProvider(provider, settings.redis_url, settings.query_cache_ttl_seconds)
