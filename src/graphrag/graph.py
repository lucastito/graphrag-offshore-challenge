"""Estrutura do knowledge graph.

Envolve um ``networkx.MultiDiGraph`` numa fachada tipada. Os nos e arestas seguem
o schema da SPEC (secao 2); ``pydantic`` valida a forma de cada no na insercao.
As consultas expostas aqui (vizinhos por tipo de aresta e travessia BFS com poda)
sao o que a recuperacao usa -- nada alem do necessario.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Iterable

import networkx as nx
from pydantic import BaseModel, ConfigDict

# Vocabulario do schema (SPEC secao 2). Mantido aqui como fonte unica de verdade.
NODE_TYPES = {
    "Cenario",
    "Decisao",
    "Restricao",
    "Propriedade",
    "Sistema",
    "ImpactoEconomico",
}
EDGE_TYPES = {"IMPACTA", "DERIVA_DE", "EXIGE", "GERA_CUSTO", "PERTENCE_A"}


class Node(BaseModel):
    """Forma validada de um no antes de entrar no grafo."""

    model_config = ConfigDict(extra="allow")

    id: str
    ntype: str
    doc: str | None = None
    cenario: str | None = None
    status: str | None = None
    aliases: list[str] = []

    def model_post_init(self, __context: Any) -> None:
        if self.ntype not in NODE_TYPES:
            raise ValueError(f"tipo de no invalido: {self.ntype!r}")


@dataclass
class KnowledgeGraph:
    g: nx.MultiDiGraph = field(default_factory=nx.MultiDiGraph)

    # -- construcao ----------------------------------------------------------

    def add_node(self, node_id: str, ntype: str, **attrs: Any) -> None:
        node = Node(id=node_id, ntype=ntype, **attrs)
        self.g.add_node(node.id, **node.model_dump(exclude={"id"}))

    def add_edge(self, src: str, dst: str, etype: str, **attrs: Any) -> None:
        if etype not in EDGE_TYPES:
            raise ValueError(f"tipo de aresta invalido: {etype!r}")
        self.g.add_edge(src, dst, etype=etype, **attrs)

    # -- consulta ------------------------------------------------------------

    def neighbors(
        self, node_id: str, etypes: Iterable[str] | None = None
    ) -> list[tuple[str, str]]:
        """Vizinhos alcancaveis a partir de ``node_id``.

        Segue arestas em ambos os sentidos (a cadeia causal e navegavel tanto da
        causa para o efeito quanto do efeito para a causa). Devolve pares
        ``(vizinho, etype)``. ``etypes`` filtra por tipo de aresta.
        """
        allowed = set(etypes) if etypes is not None else None
        out: list[tuple[str, str]] = []
        for _, dst, data in self.g.out_edges(node_id, data=True):
            et = data.get("etype")
            if allowed is None or et in allowed:
                out.append((dst, et))
        for src, _, data in self.g.in_edges(node_id, data=True):
            et = data.get("etype")
            if allowed is None or et in allowed:
                out.append((src, et))
        return out

    def bfs(
        self,
        seeds: Iterable[str],
        max_hops: int = 3,
        etypes: Iterable[str] | None = None,
        keep=None,
    ) -> list[str]:
        """Travessia em largura a partir de ``seeds``, ate ``max_hops`` saltos.

        ``etypes`` restringe os tipos de aresta seguidos. ``keep`` e um predicado
        ``(node_id, attrs) -> bool``: um vizinho so entra no subgrafo se passar --
        e a poda por cenario/vigencia (SPEC secao 4). Os proprios seeds sempre
        entram; o predicado filtra apenas a expansao.
        """
        seen: list[str] = []
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        for s in seeds:
            if s in self.g and s not in visited:
                visited.add(s)
                seen.append(s)
                queue.append((s, 0))
        while queue:
            node_id, hops = queue.popleft()
            if hops >= max_hops:
                continue
            for neighbor, _et in self.neighbors(node_id, etypes):
                if neighbor in visited:
                    continue
                attrs = self.g.nodes[neighbor]
                if keep is not None and not keep(neighbor, attrs):
                    continue
                visited.add(neighbor)
                seen.append(neighbor)
                queue.append((neighbor, hops + 1))
        return seen

    def node(self, node_id: str) -> dict[str, Any]:
        return dict(self.g.nodes[node_id])

    def docs_of(self, node_ids: Iterable[str]) -> list[str]:
        """Documentos de origem distintos dos nos dados (rastreabilidade)."""
        docs: list[str] = []
        for nid in node_ids:
            doc = self.g.nodes[nid].get("doc")
            if doc and doc not in docs:
                docs.append(doc)
        return docs
