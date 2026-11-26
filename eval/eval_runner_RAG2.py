import json
import sys
from pathlib import Path

# Ensure the project root is in Python's path so `from RAG2.agent import ask` works from anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from RAG2.agent import ask

DATASET_PATH = PROJECT_ROOT / "eval_dataset.jsonl"
OUTPUT_PATH = Path(__file__).resolve().parent / "eval_results_RAG2.json"


def load_dataset(path: Path) -> list[dict]:
    """Read questions and expected answers from a JSONL file."""
    dataset = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                dataset.append(json.loads(line))
    return dataset


def run_eval() -> list[dict]:
    """Run every question from eval_dataset.jsonl through the RAG agent and save the results."""
    dataset = load_dataset(DATASET_PATH)
    results = []

    print(f"Loaded {len(dataset)} questions from {DATASET_PATH.name}\n")

    for i, item in enumerate(dataset, start=1):
        question = item["question"]
        expected_answer = item["expected_answer"]

        print(f"[{i}/{len(dataset)}] Running: {question}")
        rag_output = ask(question)

        results.append(
            {
                "question": question,
                "expected_answer": expected_answer,
                "actual_answer": rag_output["answer"],
                "context": rag_output["context"],
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} results to {OUTPUT_PATH}")
    return results


if __name__ == "__main__":
    run_eval()
