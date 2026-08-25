from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field

from app.db.models.knowledge_document import DocumentSourceType, DocumentStatus
from app.schemas.common import ResourceSchema


class URLImportRequest(BaseModel):
    url: AnyHttpUrl


class WebsiteCrawlRequest(BaseModel):
    root_url: AnyHttpUrl
    max_pages: int = Field(default=20, ge=1, le=100)
    max_depth: int = Field(default=2, ge=0, le=5)


class DocumentRead(ResourceSchema):
    knowledge_base_id: UUID
    source_type: DocumentSourceType
    filename: str | None
    original_filename: str | None
    url: str | None
    title: str | None
    mime_type: str | None
    file_size: int | None
    status: DocumentStatus
    error_message: str | None
    content_hash: str | None
    metadata: dict[str, Any] = Field(validation_alias="document_metadata")
    processed_at: datetime | None
    chunk_count: int = 0


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    chunk_id: UUID
    content: str
    score: float
    document_id: UUID
    source: dict[str, Any]
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
