import re
from dataclasses import dataclass


@dataclass(slots=True)
class QueryAnalysis:
    is_too_short: bool
    depends_on_context: bool
    contains_time_reference: bool
    needs_rewrite: bool
    is_factual: bool


def analyze_query(query: str) -> QueryAnalysis:
    lowered = query.lower().strip()
    contextual = bool(re.search(r"\b(it|they|that|this|he|she|its|their)\b|它|这|那|其", lowered))
    temporal = bool(re.search(r"\b(19|20)\d{2}\b|last year|去年|今年|季度|quarter", lowered))
    too_short = len(lowered) < 4
    factual = bool(re.search(r"what|when|where|who|how many|多少|什么|何时|哪里|政策", lowered))
    return QueryAnalysis(too_short, contextual, temporal, contextual or too_short, factual)
