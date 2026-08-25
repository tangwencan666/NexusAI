from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ResourceSchema


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    owner_id: UUID


class WorkspaceRead(ResourceSchema):
    name: str
    description: str | None
    owner_id: UUID
