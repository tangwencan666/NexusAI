import hashlib
import json

from redis.asyncio import Redis

from app.ai.embeddings.base import EmbeddingProvider


class CachedEmbeddingProvider(EmbeddingProvider):
    def __init__(self, provider: EmbeddingProvider, redis_url: str, ttl_seconds: int) -> None:
        self.provider = provider
        self.redis = Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=0.5)
        self.ttl_seconds = ttl_seconds

    @property
    def dimension(self) -> int:
        return self.provider.dimension

    @property
    def model_name(self) -> str:
        return self.provider.model_name

    def key(self, text: str) -> str:
        digest = hashlib.sha256(f"{self.model_name}:{text}".encode()).hexdigest()
        return f"nexusai:embedding:{digest}"

    async def embed_text(self, text: str) -> list[float]:
        key = self.key(text)
        try:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        vector = await self.provider.embed_text(text)
        try:
            await self.redis.set(key, json.dumps(vector), ex=self.ttl_seconds)
        except Exception:
            pass
        return vector

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(text) for text in texts]
