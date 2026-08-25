from abc import ABC, abstractmethod

from app.knowledge.types import ParsedSection, TextChunk


class Chunker(ABC):
    @abstractmethod
    def chunk(self, sections: list[ParsedSection]) -> list[TextChunk]: ...
