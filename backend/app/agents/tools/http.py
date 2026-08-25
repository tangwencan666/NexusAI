from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.agents.tools.base import BaseTool, RiskLevel, ToolContext, ToolResult
from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.knowledge.web.security import validate_public_url


class HTTPRequestInput(BaseModel):
    method: Literal["GET", "POST"] = "GET"
    url: str
    json_body: dict | None = None
    headers: dict[str, str] = Field(default_factory=dict)


class HTTPRequestTool(BaseTool):
    name = "http_request"
    description = "Call an allowlisted public HTTP API; POST requires human approval."
    input_schema = HTTPRequestInput
    risk_level = RiskLevel.MEDIUM
    timeout_seconds = settings.http_tool_timeout_seconds

    async def execute(self, context: ToolContext, params: HTTPRequestInput) -> ToolResult:
        if params.method == "POST":
            raise ApplicationError("APPROVAL_REQUIRED", "POST requests must pass through approval", 409)
        url = await validate_public_url(params.url)
        allowed = {host.strip().lower() for host in settings.http_tool_allowed_hosts.split(",") if host.strip()}
        from urllib.parse import urlparse
        if allowed and (urlparse(url).hostname or "").lower() not in allowed:
            raise ApplicationError("HTTP_HOST_DENIED", "Host is outside the HTTP tool allowlist", 403)
        safe_headers = {key: value for key, value in params.headers.items() if key.lower() not in {"authorization", "cookie", "proxy-authorization"}}
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
            response = await client.get(url, headers=safe_headers)
            redirects = 0
            while response.is_redirect:
                redirects += 1
                if redirects > 5 or not response.headers.get("location"):
                    raise ApplicationError("HTTP_REDIRECT_FAILED", "Unsafe or excessive redirects", 422)
                next_url = str(response.url.join(response.headers["location"]))
                await validate_public_url(next_url)
                response = await client.get(next_url, headers=safe_headers)
            content = response.content[: settings.http_tool_max_response_bytes]
            content_type = response.headers.get("content-type", "")
            body = response.json() if "json" in content_type and len(response.content) <= settings.http_tool_max_response_bytes else content.decode(errors="replace")
            return ToolResult(True, {"status_code": response.status_code, "body": body}, metadata={"url": str(response.url), "truncated": len(response.content) > len(content)})


class HTTPPostTool(HTTPRequestTool):
    name = "http_post"
    description = "Perform a human-approved POST to an allowlisted public API."
    risk_level = RiskLevel.HIGH
    requires_approval = True

    async def execute(self, context: ToolContext, params: HTTPRequestInput) -> ToolResult:
        if params.method != "POST":
            params.method = "POST"
        url = await validate_public_url(params.url)
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
            response = await client.post(url, json=params.json_body, headers={k: v for k, v in params.headers.items() if k.lower() not in {"authorization", "cookie"}})
        return ToolResult(True, {"status_code": response.status_code, "body": response.text[: settings.http_tool_max_response_bytes]})
