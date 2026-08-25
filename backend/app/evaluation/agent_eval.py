import argparse
import json
from pathlib import Path


def evaluate(rows: list[dict]) -> dict[str, float]:
    total = max(1, len(rows))
    return {
        "task_completion_rate": sum(row["completed"] for row in rows) / total,
        "tool_selection_accuracy": sum(row["selected_tools"] == row["expected_tools"] for row in rows) / total,
        "tool_success_rate": sum(row["successful_tool_calls"] for row in rows) / max(1, sum(row["tool_calls"] for row in rows)),
        "average_steps": sum(row["steps"] for row in rows) / total,
        "approval_correctness": sum(row["approval_correct"] for row in rows) / total,
        "loop_rate": sum(row["looped"] for row in rows) / total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", default="evals/agent_tasks.jsonl"); args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    metrics = evaluate(rows)
    print(f"Dataset size: {len(rows)}")
    for name, value in metrics.items(): print(f"{name}: {value:.4f}")
    return 0 if metrics["task_completion_rate"] >= 0.8 and metrics["tool_selection_accuracy"] >= 0.8 else 1


if __name__ == "__main__": raise SystemExit(main())
