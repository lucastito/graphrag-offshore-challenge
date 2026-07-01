"""GraphRAG: pergunta em linguagem natural -> subgrafo relevante + contexto.

O coração do desafio. Mostre travessia REAL do grafo (multi-hop), não só
top-k de embeddings. Garanta rastreabilidade (de quais nós/docs veio a resposta).

TODO:
- Identificar nó(s) de entrada a partir da pergunta
- Traverssar o grafo coletando o subgrafo relevante
- Montar o contexto (com proveniência) para a geração da resposta
"""
from __future__ import annotations
from dataclasses import dataclass
from .graph import KnowledgeGraph


@dataclass
class Retrieval:
    context: str
    sources: list[str]  # ids de nó/documento usados (rastreabilidade)


def retrieve(kg: KnowledgeGraph, question: str) -> Retrieval:
    # TODO: implementar
    raise NotImplementedError
