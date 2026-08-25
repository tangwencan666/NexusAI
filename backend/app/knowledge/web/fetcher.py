from dataclasses import dataclass
from urllib.parse import urljoin

import httpx

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.knowledge.web.security import validate_public_url


@dataclass(slots=True)
class FetchResult:
    url: str
    content: bytes
    content_type: str


class SafeHTTPFetcher:
    async def fetch(self, url: str) -> FetchResult:
        current = url
        timeout = httpx.Timeout(
            connect=settings.url_connect_timeout_seconds,
            read=settings.url_read_timeout_seconds,
            write=settings.url_read_timeout_seconds,
            pool=settings.url_connect_timeout_seconds,
        )
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
                headers={"User-Agent": settings.crawler_user_agent, "Accept": "text/html,*/*;q=0.8"},
            ) as client:
                for redirect_count in range(settings.url_max_redirects + 1):
                    await validate_public_url(current)
                    async with client.stream("GET", current) as response:
                        if response.is_redirect:
                            if redirect_count >= settings.url_max_redirects:
                                raise ApplicationError("FETCH_FAILED", "Too many redirects", 422)
                            location = response.headers.get("location")
                            if not location:
                                raise ApplicationError("FETCH_FAILED", "Redirect has no destination", 422)
                            current = urljoin(current, location)
                            continue
                        response.raise_for_status()
                        maximum = settings.max_url_response_size_mb * 1024 * 1024
                        declared = int(response.headers.get("content-length", "0") or 0)
                        if declared > maximum:
                            raise ApplicationError("FETCH_FAILED", "URL response exceeds size limit", 413)
                        data = bytearray()
                        async for chunk in response.aiter_bytes():
                            data.extend(chunk)
                            if len(data) > maximum:
                                raise ApplicationError("FETCH_FAILED", "URL response exceeds size limit", 413)
                        return FetchResult(
                            str(response.url), bytes(data), response.headers.get("content-type", "")
                        )
        except ApplicationError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise ApplicationError("FETCH_FAILED", f"Unable to fetch URL: {exc}", 422) from exc
        raise ApplicationError("FETCH_FAILED", "Unable to fetch URL", 422)
