import uuid
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.db.models.document_chunk import DocumentChunk
from app.db.models.knowledge_document import KnowledgeDocument
from app.knowledge.retrieval.base import Retriever
from app.knowledge.retrieval.models import RetrievalResult


class BM25Retriever(Retriever):
    """PostgreSQL FTS lexical retriever using cover-density rank."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _lexical_query(query: str) -> str:
        stopwords = {
            "a", "an", "and", "are", "do", "does", "for", "have", "how", "i", "is",
            "it", "of", "on", "or", "the", "to", "what", "when", "where", "who", "why",
        }
        terms = [term for term in re.findall(r"[\w-]+", query.lower()) if term not in stopwords]
        return " OR ".join(dict.fromkeys(terms)) or query

    async def search(self, knowledge_base_id: uuid.UUID, query: str, top_k: int) -> list[RetrievalResult]:
        try:
            tsquery = func.websearch_to_tsquery("simple", self._lexical_query(query))
            lexical_score = func.ts_rank_cd(DocumentChunk.search_vector, tsquery)
            statement = (
                select(DocumentChunk, KnowledgeDocument, lexical_score.label("lexical_score"))
                .join(KnowledgeDocument, KnowledgeDocument.id == DocumentChunk.document_id)
                .where(
                    DocumentChunk.knowledge_base_id == knowledge_base_id,
                    DocumentChunk.search_vector.op("@@")(tsquery),
                )
                .order_by(lexical_score.desc())
                .limit(top_k)
            )
            rows = (await self.session.execute(statement)).all()
            results: list[RetrievalResult] = []
            for rank, (chunk, document, score) in enumerate(rows, 1):
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
                        chunk.id, document.id, chunk.content, chunk.chunk_metadata, source,
                        float(score), rank, "bm25", lexical_score=float(score), ranks={"bm25": rank}
                    )
                )
            return results
        except Exception as exc:
            raise ApplicationError("RETRIEVAL_FAILED", "PostgreSQL FTS retrieval failed", 500) from exc
