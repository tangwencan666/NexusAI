import re

from app.knowledge.citations.builder import Citation


def validate_citations(answer: str, citations: list[Citation]) -> tuple[str, list[int]]:
    valid = {citation.id for citation in citations}
    invalid: list[int] = []

    def replace(match: re.Match[str]) -> str:
        citation_id = int(match.group(1))
        if citation_id not in valid:
            invalid.append(citation_id)
            return ""
        return match.group(0)

    return re.sub(r"\[(\d+)\]", replace, answer), sorted(set(invalid))
