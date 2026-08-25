import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin
from app.db.models.knowledge_document import enum_values


class CrawlStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WebsiteCrawlJob(UUIDTimestampMixin, Base):
    __tablename__ = "website_crawl_jobs"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True
    )
    root_url: Mapped[str] = mapped_column(Text)
    max_pages: Mapped[int] = mapped_column(Integer, default=20)
    max_depth: Mapped[int] = mapped_column(Integer, default=2)
    status: Mapped[CrawlStatus] = mapped_column(
        Enum(CrawlStatus, name="crawl_status", values_callable=enum_values),
        default=CrawlStatus.PENDING,
        server_default=CrawlStatus.PENDING.value,
    )
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pages_processed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)
    crawl_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
