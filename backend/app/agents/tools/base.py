import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class ToolContext:
    session: Any
    run_id: str | None = None
    enabled_tools: set[str] = field(default_factory=set)


@dataclass(slots=True)
class ToolResult:
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0


class BaseTool(ABC):
    name: str
    description: str
    input_schema: type[BaseModel]
    risk_level = RiskLevel.LOW
    requires_approval = False
    timeout_seconds = 30.0

    @abstractmethod
    async def execute(self, context: ToolContext, params: BaseModel) -> ToolResult: ...

    async def invoke(self, context: ToolContext, arguments: dict[str, Any]) -> ToolResult:
        started = time.perf_counter()
        try:
            params = self.input_schema.model_validate(arguments)
            result = await self.execute(context, params)
        except Exception as exc:
            result = ToolResult(False, error=str(exc), metadata={"error_code": getattr(exc, "code", "TOOL_EXECUTION_FAILED")})
        result.duration_ms = (time.perf_counter() - started) * 1000
        return result

    def manifest(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema.model_json_schema(), "risk_level": self.risk_level.value, "requires_approval": self.requires_approval, "timeout_seconds": self.timeout_seconds}
