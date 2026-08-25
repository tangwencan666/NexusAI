from pathlib import Path

from app.core.exceptions import ApplicationError
from app.knowledge.parsers.base import DocumentParser
from app.knowledge.parsers.docx import DocxParser
from app.knowledge.parsers.pdf import PDFParser
from app.knowledge.parsers.text import TextParser

PARSERS: dict[str, DocumentParser] = {
    ".pdf": PDFParser(),
    ".docx": DocxParser(),
    ".txt": TextParser(),
    ".md": TextParser(),
}


def get_parser(filename: str) -> DocumentParser:
    parser = PARSERS.get(Path(filename).suffix.lower())
    if parser is None:
        raise ApplicationError(
            "UNSUPPORTED_FILE_TYPE", "Supported file types are PDF, DOCX, TXT, and MD", 415
        )
    return parser
