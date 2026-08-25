from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass

import httpx
from pydantic import BaseModel, Field

from app.agents.tools.base import BaseTool, ToolContext, ToolResult
from app.core.config import settings
from app.core.exceptions import ApplicationError


@dataclass(slots=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str
    published_at: str | None = None
    source: str = "web"


class WebSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int) -> list[WebSearchResult]: ...


class FakeWebSearchProvider(WebSearchProvider):
    async def search(self, query: str, max_results: int) -> list[WebSearchResult]:
        return [WebSearchResult(f"Result for {query}", "https://example.com/result", f"Deterministic result about {query}.", source="fake")][:max_results]


class TavilyWebSearchProvider(WebSearchProvider):
    async def search(self, query: str, max_results: int) -> list[WebSearchResult]:
        if not settings.tavily_api_key:
            raise ApplicationError("WEB_SEARCH_PROVIDER_UNAVAILABLE", "Tavily API key is not configured", 503)
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post("https://api.tavily.com/search", json={"api_key": settings.tavily_api_key, "query": query, "max_results": max_results})
            response.raise_for_status()
        return [WebSearchResult(item.get("title", ""), item.get("url", ""), item.get("content", ""), source="tavily") for item in response.json().get("results", [])]


class WebSearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    max_results: int = Field(default=5, ge=1, le=10)


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the public web through a configured provider."
    input_schema = WebSearchInput

    def __init__(self, provider: WebSearchProvider) -> None:
        self.provider = provider

    async def execute(self, context: ToolContext, params: WebSearchInput) -> ToolResult:
        return ToolResult(True, [asdict(item) for item in await self.provider.search(params.query, params.max_results)])
