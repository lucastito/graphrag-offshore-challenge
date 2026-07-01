"""CLI mínima.

Uso:
    python -m graphrag "sua pergunta"
    python -m graphrag --eval data/questions.yaml
"""
from __future__ import annotations
import sys
from .ingest import build_graph
from .agent import answer_question


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    kg = build_graph()
    if argv[0] == "--eval":
        # TODO: carregar questions.yaml e rodar todas, imprimindo resposta + fontes
        print("TODO: implementar modo --eval")
        return 0
    question = " ".join(argv)
    ans = answer_question(kg, question)
    print(ans.text)
    print("\nFontes:", ", ".join(ans.sources))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
