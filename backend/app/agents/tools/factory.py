from app.agents.tools.customer import CustomerLookupTool,OrderLookupTool,TicketListTool,TicketCreateTool,RefundPrepareTool,RefundCreateTool
from app.agents.tools.http import HTTPPostTool, HTTPRequestTool
from app.agents.tools.knowledge import KnowledgeSearchTool
from app.agents.tools.registry import ToolRegistry
from app.agents.tools.sql_readonly import SQLReadOnlyTool
from app.agents.tools.web_search import FakeWebSearchProvider, TavilyWebSearchProvider, WebSearchTool
from app.core.config import settings


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    provider = TavilyWebSearchProvider() if settings.web_search_provider == "tavily" else FakeWebSearchProvider()
    for tool in (KnowledgeSearchTool(), SQLReadOnlyTool(), HTTPRequestTool(), HTTPPostTool(), WebSearchTool(provider), CustomerLookupTool(), OrderLookupTool(), TicketListTool(), TicketCreateTool(), RefundPrepareTool(), RefundCreateTool()):
        registry.register(tool)
    return registry
