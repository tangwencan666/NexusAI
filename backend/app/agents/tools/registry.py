from __future__ import annotations

from app.agents.tools.base import BaseTool
from app.core.exceptions import ApplicationError


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str, enabled: set[str] | None = None) -> BaseTool:
        if name not in self._tools:
            raise ApplicationError("TOOL_NOT_FOUND", f"Unknown tool: {name}", 404)
        if enabled is not None and name not in enabled:
            raise ApplicationError("TOOL_PERMISSION_DENIED", f"Tool is not enabled: {name}", 403)
        return self._tools[name]

    def list(self) -> list[dict]:
        return [tool.manifest() for tool in self._tools.values()]

    def enabled_tools(self, names: set[str]) -> list[dict]:
        return [tool.manifest() for name, tool in self._tools.items() if name in names]
