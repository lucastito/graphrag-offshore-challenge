"""Avaliacao: precision/recall das fontes contra o gabarito (SPEC secao 5).

Mede a recuperacao, nao a geracao. Precision penaliza trazer distrator (falso
positivo); recall penaliza perder fonte correta (falso negativo). Neste corpus a
prioridade e precision -- as armadilhas (doc 09 do S2, Rev B) sao falsos positivos.
"""
from __future__ import annotations

from dataclasses import dataclass


def source_precision_recall(
    retrieved: list[str], gold: list[str]
) -> tuple[float, float]:
    """Precision e recall das fontes recuperadas contra as esperadas."""
    ret = set(retrieved)
    au = set(gold)
    if not ret and not au:
        return 1.0, 1.0
    tp = len(ret & au)
    precision = tp / len(ret) if ret else 0.0
    recall = tp / len(au) if au else 1.0
    return precision, recall


@dataclass
class QuestionResult:
    qid: str
    question: str
    answer_text: str
    retrieved: list[str]
    gold: list[str]
    precision: float
    recall: float


def evaluate(kg, questions: list[dict]) -> list[QuestionResult]:
    """Roda cada pergunta pelo agente e mede precision/recall das fontes.

    Cada item de ``questions`` deve ter ``id``, ``question`` e ``gold_docs``
    (lista de documentos esperados). Importado localmente para evitar ciclo.
    """
    from .agent import answer_question

    results: list[QuestionResult] = []
    for q in questions:
        ans = answer_question(kg, q["question"])
        gold = [str(d) for d in q.get("gold_docs", [])]
        p, r = source_precision_recall(ans.sources, gold)
        results.append(
            QuestionResult(
                qid=q.get("id", "?"),
                question=q["question"],
                answer_text=ans.text,
                retrieved=ans.sources,
                gold=gold,
                precision=p,
                recall=r,
            )
        )
    return results
