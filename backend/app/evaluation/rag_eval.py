import argparse
import json
from pathlib import Path

from app.core.config import settings
from app.evaluation.metrics import retrieval_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic NexusAI RAG retrieval fixtures")
    parser.add_argument("--retriever", choices=["vector", "bm25", "hybrid", "rerank"], default="hybrid")
    parser.add_argument("--dataset", default="evals/rag_retrieval.jsonl")
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line]
    ranked = [row.get(f"{args.retriever}_ranking", row["fixture_ranking"]) for row in rows]
    expected = [set(row["expected_chunk_ids"]) for row in rows]
    metrics = retrieval_metrics(ranked, expected, 5)
    print(f"Dataset size: {len(rows)}")
    print(f"Retriever: {args.retriever}")
    print(f"Recall@5: {metrics.recall_at_k:.4f}")
    print(f"HitRate@5: {metrics.hit_rate_at_k:.4f}")
    print(f"MRR: {metrics.mrr:.4f}")
    return int(metrics.recall_at_k < settings.min_recall_at_5 or metrics.mrr < settings.min_mrr)


if __name__ == "__main__":
    raise SystemExit(main())
