import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import UploadFile
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.base import EmbeddingProvider
from app.core.config import settings
from app.core.exceptions import ApplicationError, ResourceNotFoundError
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.knowledge_document import (
    DocumentSourceType,
    DocumentStatus,
    KnowledgeDocument,
)
from app.db.models.website_crawl_job import CrawlStatus, WebsiteCrawlJob
from app.knowledge.ingestion.pipeline import IngestionPipeline
from app.knowledge.parsers.factory import get_parser
from app.knowledge.parsers.html import HTMLParser
from app.knowledge.web.crawler import WebsiteCrawler
from app.knowledge.web.fetcher import SafeHTTPFetcher
from app.knowledge.web.fetcher import FetchResult
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.schemas.documents import DocumentRead
from app.storage.base import StorageProvider

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
}


class KnowledgeService:
    def __init__(
        self,
        session: AsyncSession,
        embeddings: EmbeddingProvider,
        storage: StorageProvider,
        fetcher: SafeHTTPFetcher | None = None,
    ) -> None:
        self.session = session
        self.embeddings = embeddings
        self.storage = storage
        self.fetcher = fetcher or SafeHTTPFetcher()
        self.documents = KnowledgeDocumentRepository(session)

    async def _require_knowledge_base(self, knowledge_base_id: uuid.UUID) -> None:
        if await self.session.get(KnowledgeBase, knowledge_base_id) is None:
            raise ResourceNotFoundError("Knowledge base", knowledge_base_id)

    async def upload(self, knowledge_base_id: uuid.UUID, upload: UploadFile) -> KnowledgeDocument:
        await self._require_knowledge_base(knowledge_base_id)
        original = Path(upload.filename or "").name
        suffix = Path(original).suffix.lower()
        if suffix not in ALLOWED_MIME_TYPES or upload.content_type not in ALLOWED_MIME_TYPES[suffix]:
            raise ApplicationError("UNSUPPORTED_FILE_TYPE", "Supported file types are PDF, DOCX, TXT, and MD", 415)
        document_id = uuid.uuid4()
        storage_key = f"{knowledge_base_id}/{document_id}{suffix}"
        maximum = settings.max_upload_size_mb * 1024 * 1024

        async def chunks():
            total = 0
            while data := await upload.read(1024 * 1024):
                total += len(data)
                if total > maximum:
                    raise ApplicationError("FILE_TOO_LARGE", f"File exceeds {settings.max_upload_size_mb} MB limit", 413)
                yield data

        try:
            _, size = await self.storage.save(storage_key, chunks())
        except Exception:
            await self.storage.delete(storage_key)
            raise
        document = KnowledgeDocument(
            id=document_id,
            knowledge_base_id=knowledge_base_id,
            source_type=DocumentSourceType.FILE,
            filename=f"{document_id}{suffix}",
            original_filename=original,
            storage_key=storage_key,
            mime_type=upload.content_type,
            file_size=size,
            status=DocumentStatus.PENDING,
            document_metadata={"source_type": "file", "filename": original},
        )
        self.session.add(document)
        await self.session.commit()
        content = await self.storage.read(storage_key)
        parsed = get_parser(original).parse(
            content, {"source_type": "file", "filename": original, "source": original}
        )
        return await IngestionPipeline(self.session, self.embeddings).ingest(document, parsed)

    async def import_url(
        self, knowledge_base_id: uuid.UUID, url: str, source_type: DocumentSourceType = DocumentSourceType.URL
    ) -> KnowledgeDocument:
        await self._require_knowledge_base(knowledge_base_id)
        result = await self.fetcher.fetch(url)
        return await self._ingest_web_result(knowledge_base_id, result, source_type)

    async def _ingest_web_result(
        self,
        knowledge_base_id: uuid.UUID,
        result: FetchResult,
        source_type: DocumentSourceType,
    ) -> KnowledgeDocument:
        if "html" not in result.content_type.lower():
            raise ApplicationError("DOCUMENT_PARSE_FAILED", "URL did not return HTML content", 422)
        parsed = HTMLParser().parse(result.content, result.url)
        parsed.metadata["crawled_at"] = datetime.now(UTC).isoformat()
        for section in parsed.sections:
            section.metadata["source_type"] = source_type.value
        document = KnowledgeDocument(
            knowledge_base_id=knowledge_base_id,
            source_type=source_type,
            url=result.url,
            title=parsed.title,
            mime_type=result.content_type,
            file_size=len(result.content),
            status=DocumentStatus.PENDING,
            document_metadata={**parsed.metadata, "source_type": source_type.value},
        )
        self.session.add(document)
        await self.session.commit()
        return await IngestionPipeline(self.session, self.embeddings).ingest(document, parsed)

    async def list_documents(self, knowledge_base_id: uuid.UUID) -> list[DocumentRead]:
        await self._require_knowledge_base(knowledge_base_id)
        rows = await self.documents.list_for_knowledge_base(knowledge_base_id)
        return [DocumentRead.model_validate(document).model_copy(update={"chunk_count": count}) for document, count in rows]

    async def get_document(self, document_id: uuid.UUID) -> DocumentRead:
        document = await self.documents.get(document_id)
        if document is None:
            raise ResourceNotFoundError("Document", document_id)
        rows = await self.documents.list_for_knowledge_base(document.knowledge_base_id)
        count = next((count for candidate, count in rows if candidate.id == document_id), 0)
        return DocumentRead.model_validate(document).model_copy(update={"chunk_count": count})

    async def delete_document(self, document_id: uuid.UUID) -> None:
        document = await self.documents.get(document_id)
        if document is None:
            raise ResourceNotFoundError("Document", document_id)
        storage_key = document.storage_key
        await self.session.execute(delete(KnowledgeDocument).where(KnowledgeDocument.id == document_id))
        await self.session.commit()
        if storage_key:
            try:
                await self.storage.delete(storage_key)
            except OSError as exc:
                logger.warning("storage_delete_failed document_id=%s reason=%s", document_id, exc)

    async def crawl_website(
        self, knowledge_base_id: uuid.UUID, root_url: str, max_pages: int, max_depth: int
    ) -> WebsiteCrawlJob:
        await self._require_knowledge_base(knowledge_base_id)
        job = WebsiteCrawlJob(
            knowledge_base_id=knowledge_base_id,
            root_url=root_url,
            max_pages=max_pages,
            max_depth=max_depth,
            status=CrawlStatus.PROCESSING,
        )
        self.session.add(job)
        await self.session.commit()
        try:
            pages, discovered = await WebsiteCrawler(self.fetcher).crawl(root_url, max_pages, max_depth)
            job.pages_discovered = discovered
            failures: list[str] = []
            for page in pages:
                try:
                    await self._ingest_web_result(
                        knowledge_base_id, page, DocumentSourceType.WEBSITE
                    )
                    job.pages_processed += 1
                except Exception as exc:
                    failures.append(f"{urlparse(page.url).path}: {exc}")
            job.status = CrawlStatus.COMPLETED
            job.finished_at = datetime.now(UTC)
            job.crawl_metadata = {"page_failures": failures[:20]}
            await self.session.commit()
            await self.session.refresh(job)
            return job
        except Exception as exc:
            await self.session.rollback()
            failed = await self.session.get(WebsiteCrawlJob, job.id)
            if failed:
                failed.status = CrawlStatus.FAILED
                failed.error_message = str(exc)[:2000]
                failed.finished_at = datetime.now(UTC)
                await self.session.commit()
            raise
