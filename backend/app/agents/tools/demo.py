from pydantic import BaseModel

from app.agents.tools.base import BaseTool, RiskLevel, ToolContext, ToolResult


class CreateRefundInput(BaseModel):
    order_id: str
    reason: str


class CreateRefundRequestTool(BaseTool):
    name = "refund.create"
    description = "Demo-only simulated refund creation. It never contacts a payment system."
    input_schema = CreateRefundInput
    risk_level = RiskLevel.HIGH
    requires_approval = True

    async def execute(self, context: ToolContext, params: CreateRefundInput) -> ToolResult:
        return ToolResult(True, {"simulated": True, "refund_request_id": f"DEMO-{params.order_id}", "order_id": params.order_id})
