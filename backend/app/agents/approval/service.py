import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.db.models.agent_runtime import AgentApprovalRequest, ApprovalStatus


class ApprovalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, approval_id: uuid.UUID) -> AgentApprovalRequest:
        item = await self.session.get(AgentApprovalRequest, approval_id)
        if not item:
            raise ApplicationError("APPROVAL_NOT_FOUND", "Approval request not found", 404)
        return item

    async def list(self, status: ApprovalStatus | None = None) -> list[AgentApprovalRequest]:
        statement = select(AgentApprovalRequest).order_by(AgentApprovalRequest.requested_at.desc())
        if status:
            statement = statement.where(AgentApprovalRequest.status == status)
        return list((await self.session.scalars(statement)).all())

    async def decide(self, approval_id: uuid.UUID, approved: bool, decided_by: uuid.UUID | None, reason: str | None) -> AgentApprovalRequest:
        item = await self.get(approval_id)
        if item.status != ApprovalStatus.PENDING:
            raise ApplicationError("APPROVAL_ALREADY_DECIDED", "Approval request is no longer pending", 409)
        item.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        item.decided_at = datetime.now(UTC)
        item.decided_by = decided_by
        item.decision_reason = reason
        await self.session.commit()
        await self.session.refresh(item)
        return item
