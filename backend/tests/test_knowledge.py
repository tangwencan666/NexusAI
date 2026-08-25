import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.embeddings.providers.fake import FakeEmbeddingProvider
from app.core.exceptions import ApplicationError
from app.knowledge.chunking.recursive import RecursiveTextChunker
from app.knowledge.parsers.factory import get_parser
from app.knowledge.retrieval.vector import VectorSearchService
from app.knowledge.types import ParsedSection
from app.knowledge.web.security import validate_public_url


def test_upload_txt_document() -> None:
    parsed = get_parser("handbook.txt").parse(
        b"Refund policy\n\nCustomers may request a refund within 30 days.",
        {"filename": "handbook.txt"},
    )
    chunks = RecursiveTextChunker(80, 10).chunk(parsed.sections)
    vectors = asyncio.run(FakeEmbeddingProvider(16).embed_texts([item.content for item in chunks]))
    assert chunks[0].metadata["filename"] == "handbook.txt"
    assert len(vectors) == len(chunks)
    assert all(len(vector) == 16 for vector in vectors)


def test_invalid_file_type() -> None:
    with pytest.raises(ApplicationError, match="Supported file types") as error:
        get_parser("malware.exe")
    assert error.value.code == "UNSUPPORTED_FILE_TYPE"


def test_url_validation() -> None:
    with pytest.raises(ApplicationError) as error:
        asyncio.run(validate_public_url("file:///etc/passwd"))
    assert error.value.code == "INVALID_URL"


@pytest.mark.parametrize("url", ["http://127.0.0.1", "http://10.0.0.1", "http://169.254.1.1", "http://[::1]"])
def test_private_ip_blocked(url: str) -> None:
    with pytest.raises(ApplicationError) as error:
        asyncio.run(validate_public_url(url))
    assert error.value.code == "UNSAFE_URL"


def test_chunker() -> None:
    text = "First paragraph explains the policy.\n\nSecond paragraph adds details. " * 8
    chunks = RecursiveTextChunker(120, 20).chunk([ParsedSection(text, {"page": 7})])
    assert len(chunks) > 1
    assert all(chunk.content and len(chunk.content) <= 120 for chunk in chunks)
    assert all(chunk.metadata["page"] == 7 for chunk in chunks)


def test_duplicate_content() -> None:
    provider = FakeEmbeddingProvider(24)
    first = asyncio.run(provider.embed_text("identical enterprise content"))
    second = asyncio.run(provider.embed_text("identical enterprise content"))
    other = asyncio.run(provider.embed_text("different content"))
    assert first == second
    assert first != other

    from app.db.models.knowledge_document import DocumentSourceType, KnowledgeDocument
    from app.knowledge.ingestion.pipeline import IngestionPipeline
    from app.knowledge.types import ParsedDocument

    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    document = KnowledgeDocument(
        id=uuid.uuid4(),
        knowledge_base_id=uuid.uuid4(),
        source_type=DocumentSourceType.FILE,
        document_metadata={},
    )
    pipeline = IngestionPipeline(session, provider)
    pipeline.repository.find_duplicate = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
    pipeline.repository.get = AsyncMock(return_value=None)
    with pytest.raises(ApplicationError) as error:
        asyncio.run(
            pipeline.ingest(document, ParsedDocument([ParsedSection("identical enterprise content")]))
        )
    assert error.value.code == "DUPLICATE_CONTENT"


def test_document_list_query_is_scoped() -> None:
    from app.repositories.knowledge import KnowledgeDocumentRepository

    session = MagicMock()
    result = MagicMock()
    result.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    rows = asyncio.run(KnowledgeDocumentRepository(session).list_for_knowledge_base(uuid.uuid4()))
    assert rows == []
    session.execute.assert_awaited_once()


def test_vector_search_service() -> None:
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    provider = FakeEmbeddingProvider(1536)
    hits = asyncio.run(VectorSearchService(session, provider).search(uuid.uuid4(), "refund", 5))
    assert hits == []
    session.execute.assert_awaited_once()
