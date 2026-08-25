from app.core.exceptions import ApplicationError
from app.knowledge.parsers.base import DocumentParser
from app.knowledge.types import ParsedDocument, ParsedSection


class TextParser(DocumentParser):
    def parse(self, content: bytes, metadata: dict[str, object]) -> ParsedDocument:
        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return ParsedDocument(
                    [ParsedSection(content.decode(encoding), metadata)], metadata=metadata
                )
            except UnicodeDecodeError:
                continue
        raise ApplicationError("DOCUMENT_PARSE_FAILED", "Text encoding is not supported")
