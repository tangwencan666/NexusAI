from abc import ABC, abstractmethod

from app.knowledge.types import ParsedDocument


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, content: bytes, metadata: dict[str, object]) -> ParsedDocument: ...
