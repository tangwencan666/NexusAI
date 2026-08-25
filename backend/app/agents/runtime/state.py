from typing import Any, Literal, TypedDict


AgentStatus = Literal["pending", "planning", "running", "waiting_approval", "completed", "failed", "cancelled"]


class AgentState(TypedDict, total=False):
    messages: list[dict[str, str]]
    user_request: str
    knowledge_base_id: str | None
    plan: dict[str, Any]
    current_step: int
    completed_steps: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    observations: list[str]
    working_memory: dict[str, Any]
    citations: list[dict[str, Any]]
    approval_required: bool
    approval_request_id: str | None
    retry_count: int
    step_count: int
    status: AgentStatus
    final_answer: str | None
    error: str | None
    route: str
    enabled_tools: list[str]
    run_id: str
