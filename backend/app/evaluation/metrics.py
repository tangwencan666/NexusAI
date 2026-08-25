from dataclasses import dataclass


@dataclass(slots=True)
class RetrievalMetrics:
    recall_at_k: float
    hit_rate_at_k: float
    mrr: float


def retrieval_metrics(
    ranked_results: list[list[str]], expected_results: list[set[str]], k: int
) -> RetrievalMetrics:
    if not expected_results:
        return RetrievalMetrics(0.0, 0.0, 0.0)
    recalls: list[float] = []
    hits: list[float] = []
    reciprocal_ranks: list[float] = []
    for ranked, expected in zip(ranked_results, expected_results, strict=True):
        top = ranked[:k]
        relevant = len(set(top) & expected)
        recalls.append(relevant / max(1, len(expected)))
        hits.append(float(relevant > 0))
        reciprocal_ranks.append(next((1 / rank for rank, item in enumerate(ranked, 1) if item in expected), 0.0))
    size = len(expected_results)
    return RetrievalMetrics(sum(recalls) / size, sum(hits) / size, sum(reciprocal_ranks) / size)


def answer_metrics(answers: list[str], valid_citation_ids: list[set[int]]) -> dict[str, float]:
    import re

    if not answers:
        return {"citation_validity": 0.0, "contains_citation": 0.0, "empty_answer_rate": 0.0}
    valid_count = total_citations = contains = empty = 0
    for answer, valid in zip(answers, valid_citation_ids, strict=True):
        ids = [int(item) for item in re.findall(r"\[(\d+)\]", answer)]
        total_citations += len(ids)
        valid_count += sum(item in valid for item in ids)
        contains += bool(ids)
        empty += not answer.strip()
    return {
        "citation_validity": valid_count / max(1, total_citations),
        "contains_citation": contains / len(answers),
        "empty_answer_rate": empty / len(answers),
    }
