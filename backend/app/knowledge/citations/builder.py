from dataclasses import dataclass

from app.knowledge.context.builder import BuiltContext


@dataclass(slots=True)
class Citation:
    id: int
    document_id: object
    chunk_id: object
    source_type: str | None
    title: str | None
    filename: str | None
    page: int | None
    url: str | None
    domain: str | None


def build_citations(context: BuiltContext) -> list[Citation]:
    return [
        Citation(
            source.citation_id,
            source.result.document_id,
            source.result.chunk_id,
            source.result.source.get("type"),
            source.result.source.get("title"),
            source.result.source.get("filename"),
            source.result.source.get("page"),
            source.result.source.get("url"),
            source.result.source.get("domain"),
        )
        for source in context.sources
    ]
