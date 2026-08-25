import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document_chunk import DocumentChunk
from app.db.models.knowledge_document import DocumentStatus, KnowledgeDocument


class KnowledgeDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, document_id: uuid.UUID) -> KnowledgeDocument | None:
        return await self.session.get(KnowledgeDocument, document_id)

    async def list_for_knowledge_base(self, knowledge_base_id: uuid.UUID) -> list[tuple[KnowledgeDocument, int]]:
        statement = (
            select(KnowledgeDocument, func.count(DocumentChunk.id))
            .outerjoin(DocumentChunk, DocumentChunk.document_id == KnowledgeDocument.id)
            .where(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
            .group_by(KnowledgeDocument.id)
            .order_by(KnowledgeDocument.created_at.desc())
        )
        return [(row[0], row[1]) for row in (await self.session.execute(statement)).all()]

    async def find_duplicate(
        self, knowledge_base_id: uuid.UUID, content_hash: str, exclude_id: uuid.UUID
    ) -> KnowledgeDocument | None:
        statement = select(KnowledgeDocument).where(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id,
            KnowledgeDocument.content_hash == content_hash,
            KnowledgeDocument.id != exclude_id,
            KnowledgeDocument.status == DocumentStatus.READY,
        )
        return await self.session.scalar(statement)

    async def clear_chunks(self, document_id: uuid.UUID) -> None:
        await self.session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
