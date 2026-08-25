from dataclasses import replace

from app.knowledge.retrieval.models import RetrievalResult


def reciprocal_rank_fusion(
    result_sets: list[list[RetrievalResult]], rrf_k: int = 60, top_k: int | None = None
) -> list[RetrievalResult]:
    fused: dict[object, RetrievalResult] = {}
    scores: dict[object, float] = {}
    for results in result_sets:
        for result in results:
            existing = fused.get(result.chunk_id)
            if existing is None:
                existing = replace(result, ranks=dict(result.ranks))
                fused[result.chunk_id] = existing
                scores[result.chunk_id] = 0.0
            scores[result.chunk_id] += 1.0 / (rrf_k + result.rank)
            existing.ranks.update(result.ranks)
            existing.vector_score = existing.vector_score or result.vector_score
            existing.lexical_score = existing.lexical_score or result.lexical_score
    ordered = sorted(fused.values(), key=lambda item: scores[item.chunk_id], reverse=True)
    if top_k is not None:
        ordered = ordered[:top_k]
    for rank, result in enumerate(ordered, 1):
        result.rank = rank
        result.score = scores[result.chunk_id]
        result.rrf_score = scores[result.chunk_id]
        result.retrieval_method = "hybrid"
    return ordered
