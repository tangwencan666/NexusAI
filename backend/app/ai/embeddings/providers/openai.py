from openai import AsyncOpenAI

from app.ai.embeddings.base import EmbeddingProvider
from app.core.exceptions import ApplicationError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str | None, model: str, dimension: int) -> None:
        self.api_key = api_key
        self._model = model
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    def _client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise ApplicationError(
                "EMBEDDING_PROVIDER_UNAVAILABLE",
                "OPENAI_API_KEY is not configured",
                503,
            )
        return AsyncOpenAI(api_key=self.api_key)

    async def embed_text(self, text: str) -> list[float]:
        return (await self.embed_texts([text]))[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self._client().embeddings.create(
                model=self._model, input=texts, dimensions=self._dimension
            )
            return [item.embedding for item in response.data]
        except ApplicationError:
            raise
        except Exception as exc:
            raise ApplicationError("EMBEDDING_FAILED", f"Embedding request failed: {exc}", 502) from exc
