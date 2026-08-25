from io import BytesIO

from docx import Document

from app.core.exceptions import ApplicationError
from app.knowledge.parsers.base import DocumentParser
from app.knowledge.types import ParsedDocument, ParsedSection


class DocxParser(DocumentParser):
    def parse(self, content: bytes, metadata: dict[str, object]) -> ParsedDocument:
        try:
            document = Document(BytesIO(content))
            paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
            return ParsedDocument([ParsedSection("\n\n".join(paragraphs), metadata)], metadata=metadata)
        except Exception as exc:
            raise ApplicationError("DOCUMENT_PARSE_FAILED", "Failed to parse DOCX") from exc
