import json
import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.approval.service import ApprovalService
from app.agents.runtime.executor import AgentRuntime
from app.agents.tools.factory import build_tool_registry
from app.core.exceptions import ApplicationError
from app.db.models.agent import Agent
from app.db.models.agent_runtime import AgentApprovalRequest, AgentRun, AgentRunStatus, ApprovalStatus
from app.db.session import get_db
from app.schemas.agent_runtime import ApprovalDecision, ApprovalRead, RunCreate, RunRead

router = APIRouter(tags=["agent-runtime"])


def event(name: str, data: object) -> str:
    return f"event: {name}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"


async def create_and_execute(agent_id: uuid.UUID, payload: RunCreate, db: AsyncSession) -> tuple[AgentRun, dict]:
    agent = await db.get(Agent, agent_id)
    if not agent or not agent.is_active:
        raise ApplicationError("AGENT_NOT_FOUND", "Active agent not found", 404)
    run = AgentRun(agent_id=agent.id, workspace_id=agent.workspace_id, input=payload.message, model_provider=agent.model_provider, model_name=agent.model_name)
    db.add(run); await db.flush()
    state = await AgentRuntime(db, build_tool_registry()).execute(run, agent.enabled_tools, str(payload.knowledge_base_id) if payload.knowledge_base_id else None)
    return run, state


@router.post("/agents/{agent_id}/runs", response_model=RunRead)
async def run_agent(agent_id: uuid.UUID, payload: RunCreate, db: AsyncSession = Depends(get_db)) -> AgentRun:
    return (await create_and_execute(agent_id, payload, db))[0]


@router.post("/agents/{agent_id}/runs/stream")
async def stream_agent(agent_id: uuid.UUID, payload: RunCreate, request: Request, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    async def generate():
        yield event("run_started", {"agent_id": agent_id})
        try:
            run, state = await create_and_execute(agent_id, payload, db)
            yield event("plan", state.get("plan", {}))
            for call in state.get("tool_calls", []):
                if await request.is_disconnected(): return
                yield event("tool_call", call)
            for result in state.get("tool_results", []): yield event("tool_result", result)
            for citation in state.get("citations", []): yield event("citation", citation)
            if state.get("status") == "waiting_approval": yield event("approval_required", {"id": state.get("approval_request_id")})
            elif state.get("status") == "completed":
                for token in (state.get("final_answer") or "").split(): yield event("token", {"text": token + " "})
                yield event("run_completed", {"run_id": run.id, "steps": run.step_count})
            else: yield event("run_failed", {"run_id": run.id, "error": run.error})
        except Exception as exc:
            yield event("run_failed", {"code": getattr(exc, "code", "AGENT_RUN_FAILED"), "message": str(exc)})
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/agent-runs", response_model=list[RunRead])
async def list_runs(limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)) -> list[AgentRun]:
    return list((await db.scalars(select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit))).all())


@router.get("/agent-runs/{run_id}", response_model=RunRead)
async def get_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> AgentRun:
    run = await db.get(AgentRun, run_id)
    if not run: raise ApplicationError("AGENT_RUN_NOT_FOUND", "Agent run not found", 404)
    return run


@router.post("/agent-runs/{run_id}/resume", response_model=RunRead)
async def resume_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> AgentRun:
    run = await db.get(AgentRun, run_id)
    if not run: raise ApplicationError("AGENT_RUN_NOT_FOUND", "Agent run not found", 404)
    await AgentRuntime(db, build_tool_registry()).resume(run)
    return run


@router.get("/agent-approvals", response_model=list[ApprovalRead])
async def list_approvals(status: ApprovalStatus | None = None, db: AsyncSession = Depends(get_db)) -> list[AgentApprovalRequest]:
    return await ApprovalService(db).list(status)


@router.get("/agent-approvals/{approval_id}", response_model=ApprovalRead)
async def get_approval(approval_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> AgentApprovalRequest:
    return await ApprovalService(db).get(approval_id)


@router.post("/agent-approvals/{approval_id}/approve", response_model=ApprovalRead)
async def approve(approval_id: uuid.UUID, payload: ApprovalDecision, db: AsyncSession = Depends(get_db)) -> AgentApprovalRequest:
    return await ApprovalService(db).decide(approval_id, True, payload.decided_by, payload.reason)


@router.post("/agent-approvals/{approval_id}/reject", response_model=ApprovalRead)
async def reject(approval_id: uuid.UUID, payload: ApprovalDecision, db: AsyncSession = Depends(get_db)) -> AgentApprovalRequest:
    return await ApprovalService(db).decide(approval_id, False, payload.decided_by, payload.reason)


@router.get("/tools")
async def list_tools() -> list[dict]:
    return build_tool_registry().list()
