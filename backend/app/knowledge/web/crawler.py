import logging
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

from lxml import html

from app.core.config import settings
from app.knowledge.web.fetcher import FetchResult, SafeHTTPFetcher

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    clean, _fragment = urldefrag(url)
    parsed = urlparse(clean)
    path = parsed.path or "/"
    return parsed._replace(path=path, fragment="").geturl()


class WebsiteCrawler:
    def __init__(self, fetcher: SafeHTTPFetcher | None = None) -> None:
        self.fetcher = fetcher or SafeHTTPFetcher()

    async def _robots(self, root_url: str) -> RobotFileParser:
        parsed = urlparse(root_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser(robots_url)
        try:
            result = await self.fetcher.fetch(robots_url)
            parser.parse(result.content.decode("utf-8", errors="replace").splitlines())
        except Exception:
            parser.parse([])
        return parser

    def _links(self, page: FetchResult, domain: str) -> set[str]:
        try:
            tree = html.fromstring(page.content, base_url=page.url)
            links = {normalize_url(urljoin(page.url, link)) for link in tree.xpath("//a/@href")}
            return {
                link
                for link in links
                if urlparse(link).scheme in {"http", "https"}
                and urlparse(link).hostname == domain
            }
        except Exception:
            return set()

    async def crawl(self, root_url: str, max_pages: int, max_depth: int) -> tuple[list[FetchResult], int]:
        root = normalize_url(root_url)
        domain = urlparse(root).hostname
        robots = await self._robots(root)
        queue: deque[tuple[str, int]] = deque([(root, 0)])
        seen = {root}
        pages: list[FetchResult] = []
        while queue and len(pages) < max_pages:
            url, depth = queue.popleft()
            if not robots.can_fetch(settings.crawler_user_agent, url):
                logger.info("crawl_skipped robots_disallowed url=%s", url)
                continue
            try:
                page = await self.fetcher.fetch(url)
                pages.append(page)
            except Exception as exc:
                logger.warning("crawl_page_failed url=%s reason=%s", url, exc)
                continue
            if depth >= max_depth:
                continue
            for link in sorted(self._links(page, domain or "")):
                if link not in seen:
                    seen.add(link)
                    queue.append((link, depth + 1))
        return pages, len(seen)
