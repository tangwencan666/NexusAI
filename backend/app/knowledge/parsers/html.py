from urllib.parse import urlparse

import trafilatura
from trafilatura.metadata import extract_metadata

from app.core.exceptions import ApplicationError
from app.knowledge.types import ParsedDocument, ParsedSection


class HTMLParser:
    def parse(self, content: bytes, url: str) -> ParsedDocument:
        try:
            html = content.decode("utf-8", errors="replace")
            text = trafilatura.extract(
                html, url=url, include_comments=False, include_tables=True, favor_precision=True
            )
            if not text:
                raise ValueError("No main content was extracted")
            extracted = extract_metadata(html, default_url=url)
            title = extracted.title if extracted else None
            domain = urlparse(url).hostname
            metadata = {
                "source_type": "url",
                "url": url,
                "title": title,
                "domain": domain,
                "published_date": extracted.date if extracted else None,
            }
            return ParsedDocument([ParsedSection(text, metadata)], title, metadata)
        except Exception as exc:
            raise ApplicationError("DOCUMENT_PARSE_FAILED", "Failed to extract webpage content") from exc
