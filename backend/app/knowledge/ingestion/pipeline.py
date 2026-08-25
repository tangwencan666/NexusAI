import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.base import EmbeddingProvider
from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.db.models.document_chunk import DocumentChunk
from app.db.models.knowledge_document import DocumentStatus, KnowledgeDocument
from app.knowledge.chunking.recursive import RecursiveTextChunker
from app.knowledge.cleaning.text import clean_text
from app.knowledge.types import ParsedDocument, ParsedSection
from app.knowledge.security.prompt_injection import prompt_injection_risk
from app.repositories.knowledge import KnowledgeDocumentRepository

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self, session: AsyncSession, embedding_provider: EmbeddingProvider) -> None:
        self.session = session
        self.embedding_provider = embedding_provider
        self.repository = KnowledgeDocumentRepository(session)
        self.chunker = RecursiveTextChunker(settings.chunk_size, settings.chunk_overlap)

    async def ingest(self, document: KnowledgeDocument, parsed: ParsedDocument) -> KnowledgeDocument:
        document.status = DocumentStatus.PROCESSING
        document.error_message = None
        await self.session.commit()
        logger.info("ingestion_started document_id=%s source=%s", document.id, document.source_type.value)
        try:
            sections = [
                ParsedSection(cleaned, section.metadata)
                for section in parsed.sections
                if (cleaned := clean_text(section.text))
            ]
            primary_content = "\n\n".join(section.text for section in sections)
            if not primary_content:
                raise ApplicationError("DOCUMENT_PARSE_FAILED", "Document contains no extractable text")
            content_hash = hashlib.sha256(primary_content.encode("utf-8")).hexdigest()
            duplicate = await self.repository.find_duplicate(
                document.knowledge_base_id, content_hash, document.id
            )
            if duplicate:
                raise ApplicationError(
                    "DUPLICATE_CONTENT",
                    f"Identical content already exists as document {duplicate.id}",
                    409,
                )
            chunks = self.chunker.chunk(sections)
            logger.info("chunks_generated document_id=%s count=%d", document.id, len(chunks))
            embeddings = await self.embedding_provider.embed_texts([chunk.content for chunk in chunks])
            if len(embeddings) != len(chunks) or any(
                len(vector) != self.embedding_provider.dimension for vector in embeddings
            ):
                raise ApplicationError("EMBEDDING_FAILED", "Embedding provider returned invalid vectors", 502)
            await self.repository.clear_chunks(document.id)
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                metadata: dict[str, Any] = {
                    **chunk.metadata,
                    "document_id": str(document.id),
                    "chunk_index": index,
                    **prompt_injection_risk(chunk.content),
                }
                self.session.add(
                    DocumentChunk(
                        document_id=document.id,
                        knowledge_base_id=document.knowledge_base_id,
                        chunk_index=index,
                        content=chunk.content,
                        token_count=max(1, len(chunk.content) // 4),
                        chunk_metadata=metadata,
                        embedding=embedding,
                    )
                )
            document.content_hash = content_hash
            document.title = document.title or parsed.title
            document.document_metadata = {**document.document_metadata, **parsed.metadata}
            document.status = DocumentStatus.READY
            document.processed_at = datetime.now(UTC)
            await self.session.commit()
            await self.session.refresh(document)
            logger.info("ingestion_completed document_id=%s embedding_count=%d", document.id, len(embeddings))
            return document
        except Exception as exc:
            await self.session.rollback()
            failed = await self.repository.get(document.id)
            if failed:
                await self.repository.clear_chunks(failed.id)
                failed.status = DocumentStatus.FAILED
                failed.error_message = str(exc)[:2000]
                await self.session.commit()
            logger.exception("ingestion_failed document_id=%s reason=%s", document.id, exc)
            raise
