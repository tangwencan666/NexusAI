from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    knowledge_base_id: UUID | None = None
    debug: bool = False


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    agent_id: UUID | None
    workspace_id: UUID
    status: str
    input: str
    final_answer: str | None
    error: str | None
    step_count: int
    total_duration_ms: float | None
    state: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ApprovalDecision(BaseModel):
    decided_by: UUID | None = None
    reason: str | None = Field(default=None, max_length=2000)


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    agent_run_id: UUID
    tool_call_id: str
    tool_name: str
    action_description: str
    arguments: dict[str, Any]
    risk_level: str
    status: str
    requested_at: datetime
    decided_at: datetime | None
    decided_by: UUID | None
    decision_reason: str | None
