from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.knowledge_base import KnowledgeBaseStatus
from app.schemas.common import ResourceSchema


class KnowledgeBaseCreate(BaseModel):
    workspace_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: KnowledgeBaseStatus = KnowledgeBaseStatus.ACTIVE


class KnowledgeBaseRead(ResourceSchema):
    workspace_id: UUID
    name: str
    description: str | None
    status: KnowledgeBaseStatus
