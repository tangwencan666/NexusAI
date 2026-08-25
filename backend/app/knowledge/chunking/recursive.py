import re

from app.knowledge.chunking.base import Chunker
from app.knowledge.types import ParsedSection, TextChunk


class RecursiveTextChunker(Chunker):
    def __init__(self, chunk_size: int, overlap: int) -> None:
        if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("Chunk size must be positive and overlap smaller than chunk size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split(self, text: str) -> list[str]:
        units = [unit.strip() for unit in re.split(r"\n\s*\n|(?<=[.!?。！？])\s+", text) if unit.strip()]
        chunks: list[str] = []
        current = ""
        for unit in units:
            pieces = [unit[i : i + self.chunk_size] for i in range(0, len(unit), self.chunk_size)]
            for piece in pieces:
                candidate = f"{current}\n\n{piece}".strip() if current else piece
                if len(candidate) <= self.chunk_size:
                    current = candidate
                    continue
                if current:
                    chunks.append(current)
                    prefix = current[-self.overlap :] if self.overlap else ""
                    current = f"{prefix} {piece}".strip()
                else:
                    chunks.append(piece)
        if current:
            chunks.append(current)
        return chunks

    def chunk(self, sections: list[ParsedSection]) -> list[TextChunk]:
        result: list[TextChunk] = []
        for section in sections:
            for content in self._split(section.text):
                result.append(TextChunk(content, dict(section.metadata)))
        return result
