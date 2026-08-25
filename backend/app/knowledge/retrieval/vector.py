import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.base import EmbeddingProvider
from app.core.exceptions import ApplicationError
from app.db.models.document_chunk import DocumentChunk
from app.db.models.knowledge_document import KnowledgeDocument
from app.knowledge.retrieval.base import Retriever
from app.knowledge.retrieval.models import RetrievalResult


class VectorSearchService(Retriever):
    def __init__(self, session: AsyncSession, provider: EmbeddingProvider) -> None:
        self.session = session
        self.provider = provider

    async def search(self, knowledge_base_id: uuid.UUID, query: str, top_k: int) -> list[RetrievalResult]:
        try:
            query_vector = await self.provider.embed_text(query)
            distance = DocumentChunk.embedding.cosine_distance(query_vector)
            statement = (
                select(DocumentChunk, KnowledgeDocument, distance.label("distance"))
                .join(KnowledgeDocument, KnowledgeDocument.id == DocumentChunk.document_id)
                .where(DocumentChunk.knowledge_base_id == knowledge_base_id)
                .order_by(distance)
                .limit(top_k)
            )
            rows = (await self.session.execute(statement)).all()
            results: list[RetrievalResult] = []
            for rank, (chunk, document, cosine_distance) in enumerate(rows, 1):
                source = {
                    "type": document.source_type.value,
                    "filename": document.original_filename or document.filename,
                    "url": document.url,
                    "title": document.title,
                    "domain": document.document_metadata.get("domain"),
                    "page": chunk.chunk_metadata.get("page"),
                }
                results.append(
                    RetrievalResult(
                        chunk_id=chunk.id,
                        document_id=document.id,
                        content=chunk.content,
                        metadata=chunk.chunk_metadata,
                        source=source,
                        score=max(0.0, min(1.0, 1.0 - float(cosine_distance))),
                        rank=rank,
                        retrieval_method="vector",
                        vector_score=max(0.0, min(1.0, 1.0 - float(cosine_distance))),
                        ranks={"vector": rank},
                    )
                )
            return results
        except ApplicationError:
            raise
        except Exception as exc:
            raise ApplicationError("VECTOR_SEARCH_FAILED", "Vector search failed", 500) from exc
