from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ResourceSchema


class AgentCreate(BaseModel):
    workspace_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    system_prompt: str = ""
    model_provider: str = Field(min_length=1, max_length=100)
    model_name: str = Field(min_length=1, max_length=100)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_steps: int = Field(default=10, ge=1, le=100)
    is_active: bool = True
    enabled_tools: list[str] = Field(default_factory=list)


class AgentRead(ResourceSchema):
    workspace_id: UUID
    name: str
    description: str | None
    system_prompt: str
    model_provider: str
    model_name: str
    temperature: float
    max_steps: int
    is_active: bool
    enabled_tools: list[str]
