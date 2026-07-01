"""Estrutura do knowledge graph.

Você pode usar networkx diretamente ou envolver em uma classe tipada.
Este arquivo dá um ponto de partida MÍNIMO — sinta-se livre para reescrever.
Defina seus tipos de nó/aresta na SPEC.md primeiro.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import networkx as nx


@dataclass
class KnowledgeGraph:
    g: nx.MultiDiGraph = field(default_factory=nx.MultiDiGraph)

    def add_node(self, node_id: str, ntype: str, **attrs: Any) -> None:
        self.g.add_node(node_id, ntype=ntype, **attrs)

    def add_edge(self, src: str, dst: str, etype: str, **attrs: Any) -> None:
        self.g.add_edge(src, dst, etype=etype, **attrs)

    # TODO: métodos de consulta que sua estratégia de recuperação precisar
    # (ex.: vizinhos por tipo de aresta, travessia multi-hop, subgrafo a partir
    # de um conjunto de nós-semente).
