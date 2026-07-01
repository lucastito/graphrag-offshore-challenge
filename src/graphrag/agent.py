"""Agente: orquestra retrieve() + geração da resposta final."""
from __future__ import annotations
from dataclasses import dataclass
from .graph import KnowledgeGraph
from .retrieve import retrieve


@dataclass
class Answer:
    text: str
    sources: list[str]


def answer_question(kg: KnowledgeGraph, question: str) -> Answer:
    r = retrieve(kg, question)
    # TODO: gerar a resposta a partir de r.context (LLM ou template),
    # mantendo r.sources como rastreabilidade.
    raise NotImplementedError
