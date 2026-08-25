from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ParsedSection:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    sections: list[ParsedSection]
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TextChunk:
    content: str
    metadata: dict[str, Any]
