"""Agente: orquestra retrieve() + geracao da resposta final.

A resposta e montada por template deterministico a partir do subgrafo recuperado
(SPEC secao 4): sem LLM, portanto fiel por construcao -- nao ha espaco para
alucinar, pois so reproduz os fatos dos nos e cita seus documentos. As sementes da
recuperacao dao a resposta direta; os demais nos do subgrafo narram a cadeia causal.
"""
from __future__ import annotations

from dataclasses import dataclass

from .graph import KnowledgeGraph
from .retrieve import Retrieval, retrieve


@dataclass
class Answer:
    text: str
    sources: list[str]
    retrieval: Retrieval | None = None


def answer_question(kg: KnowledgeGraph, question: str) -> Answer:
    r = retrieve(kg, question)

    if not r.subgraph:
        return Answer(
            text="Nao encontrei no grafo entidades que respondam a esta pergunta.",
            sources=[],
            retrieval=r,
        )

    # Resposta direta: descricoes das sementes (o que a pergunta pediu diretamente).
    direct = []
    for nid in r.seeds:
        if nid in r.subgraph:
            attrs = kg.g.nodes[nid]
            desc = attrs.get("descricao") or attrs.get("nome") or nid
            direct.append(f"{desc} (doc {attrs.get('doc', '?')})")

    # Cadeia de apoio: demais nos do subgrafo, para as perguntas multi-hop.
    support = []
    seed_set = set(r.seeds)
    for nid in r.subgraph:
        if nid in seed_set:
            continue
        attrs = kg.g.nodes[nid]
        desc = attrs.get("descricao") or attrs.get("nome")
        if desc:
            support.append(f"- {desc} (doc {attrs.get('doc', '?')})")

    parts = []
    if r.hypothetical_revb:
        parts.append("[Cenario hipotetico: Rev B proposta, ainda NAO aprovada.]")
    parts.append("Resposta: " + "; ".join(direct) + ".")
    if support:
        parts.append("Cadeia de evidencias:")
        parts.append("\n".join(support))
    parts.append("Fontes: " + ", ".join(f"doc {d}" for d in r.sources) + ".")

    return Answer(text="\n".join(parts), sources=r.sources, retrieval=r)
