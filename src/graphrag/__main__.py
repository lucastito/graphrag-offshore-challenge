"""CLI do agente GraphRAG.

Uso:
    python -m graphrag "sua pergunta"
    python -m graphrag --eval data/questions.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from .agent import answer_question
from .eval import evaluate
from .ingest import build_graph

GOLD_FILE = Path(__file__).resolve().parents[2] / "data" / "gold_sources.yaml"


def _run_eval(questions_path: str) -> int:
    kg = build_graph()
    questions = yaml.safe_load(Path(questions_path).read_text(encoding="utf-8"))
    gold = {}
    if GOLD_FILE.exists():
        gold = yaml.safe_load(GOLD_FILE.read_text(encoding="utf-8")) or {}
    for q in questions:
        q["gold_docs"] = gold.get(q["id"], [])

    results = evaluate(kg, questions)
    p_sum = r_sum = 0.0
    for res in results:
        print(f"\n[{res.qid}] {res.question}")
        print(res.answer_text)
        print(f"  fontes recuperadas: {res.retrieved}")
        print(f"  fontes esperadas:   {res.gold}")
        print(f"  precision={res.precision:.2f}  recall={res.recall:.2f}")
        p_sum += res.precision
        r_sum += res.recall
    n = len(results) or 1
    print(f"\n== media: precision={p_sum / n:.2f}  recall={r_sum / n:.2f} ==")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == "--eval":
        path = argv[1] if len(argv) > 1 else "data/questions.yaml"
        return _run_eval(path)
    kg = build_graph()
    ans = answer_question(kg, " ".join(argv))
    print(ans.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
