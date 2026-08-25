import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import ApplicationError


class PlanStep(BaseModel):
    id: int
    description: str
    tool_hint: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)


class AgentPlan(BaseModel):
    goal: str
    steps: list[PlanStep]


class Planner(ABC):
    @abstractmethod
    async def plan(self, request: str, tools: list[dict], knowledge_base_id: str | None) -> AgentPlan: ...


class FakePlanner(Planner):
    async def plan(self, request: str, tools: list[dict], knowledge_base_id: str | None) -> AgentPlan:
        available = {item["name"] for item in tools}
        lowered = request.lower()
        steps: list[PlanStep] = []
        customer = re.search(r"\bC\d+\b", request, re.I)
        order = re.search(r"\bO[A-Z0-9]+\b", request, re.I)
        if customer and "customer.lookup" in available:
            steps.append(PlanStep(id=len(steps) + 1, description="Look up customer profile", tool_hint="customer.lookup", arguments={"customer_code": customer.group(0).upper()}))
        if customer and "order.lookup" in available:
            steps.append(PlanStep(id=len(steps) + 1, description="Look up latest customer order", tool_hint="order.lookup", arguments={"customer_code": customer.group(0).upper(), "latest": True}))
        if customer and "sql_readonly" in available:
            steps.append(PlanStep(id=len(steps) + 1, description="Query recent customer orders", tool_hint="sql_readonly", arguments={"sql": f"SELECT order_id, customer_id, amount, status, ordered_at FROM demo_orders WHERE customer_id = '{customer.group(0).upper()}' ORDER BY ordered_at DESC"}))
        if knowledge_base_id and "knowledge_search" in available and any(word in lowered for word in ("policy", "refund", "knowledge", "政策", "退款")):
            steps.append(PlanStep(id=len(steps) + 1, description="Retrieve relevant knowledge-base policy", tool_hint="knowledge_search", arguments={"knowledge_base_id": knowledge_base_id, "query": request, "top_k": 5}))
        if customer and "refund.prepare" in available and any(word in lowered for word in ("refund", "退款")):
            steps.append(PlanStep(id=len(steps) + 1, description="Prepare refund eligibility", tool_hint="refund.prepare", arguments={"customer_code": customer.group(0).upper(), "reason": request}))
        if any(word in lowered for word in ("create refund", "创建退款", "refund request")) and "refund.create" in available:
            steps.append(PlanStep(id=len(steps) + 1, description="Create a refund request", tool_hint="refund.create", arguments={"order_code": order.group(0).upper() if order else "O10001", "reason": request}))
        if not steps:
            steps.append(PlanStep(id=1, description="Answer directly from the supplied request"))
        return AgentPlan(goal=request, steps=steps)


class TextToSQLService:
    async def generate(self, question: str, schema_context: str) -> dict[str, str]:
        raise ApplicationError("LLM_PROVIDER_UNAVAILABLE", "Text-to-SQL requires a configured LLM provider", 503)
