import pymupdf

from app.core.exceptions import ApplicationError
from app.knowledge.parsers.base import DocumentParser
from app.knowledge.types import ParsedDocument, ParsedSection


class PDFParser(DocumentParser):
    def parse(self, content: bytes, metadata: dict[str, object]) -> ParsedDocument:
        try:
            document = pymupdf.open(stream=content, filetype="pdf")
            sections = [
                ParsedSection(page.get_text("text"), {**metadata, "page": index + 1})
                for index, page in enumerate(document)
                if page.get_text("text").strip()
            ]
            title = document.metadata.get("title") or None
            document.close()
            return ParsedDocument(sections, title, metadata)
        except Exception as exc:
            raise ApplicationError("DOCUMENT_PARSE_FAILED", "Failed to parse PDF") from exc
