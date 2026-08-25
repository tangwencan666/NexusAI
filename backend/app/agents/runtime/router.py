from abc import ABC, abstractmethod


class Router(ABC):
    @abstractmethod
    async def route(self, request: str) -> str: ...


class FakeRouter(Router):
    async def route(self, request: str) -> str:
        value = request.lower()
        if any(word in value for word in ("order", "customer", "sql", "订单", "客户")):
            return "data_task"
        if any(word in value for word in ("knowledge", "policy", "知识", "政策")):
            return "knowledge_task"
        if any(word in value for word in ("http", "search", "refund request", "搜索", "创建")):
            return "tool_task"
        return "simple_task"
