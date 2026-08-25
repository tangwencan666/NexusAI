from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.db.models.website_crawl_job import CrawlStatus
from app.schemas.common import ResourceSchema


class CrawlJobRead(ResourceSchema):
    knowledge_base_id: UUID
    root_url: str
    max_pages: int
    max_depth: int
    status: CrawlStatus
    pages_discovered: int
    pages_processed: int
    error_message: str | None
    metadata: dict[str, Any] = Field(validation_alias="crawl_metadata")
    finished_at: datetime | None
