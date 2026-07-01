"""GraphRAG: pergunta em linguagem natural -> subgrafo relevante + contexto.

Fase 2 do GraphRAG (SPEC secao 4): o grafo ja existe; aqui apenas entramos nele e
percorremos. Tres passos: (1) achar o(s) no(s) de entrada por keyword matching
contra os aliases dos nos; (2) decidir o filtro de cenario e de vigencia a partir
da pergunta; (3) BFS com poda, coletando o subgrafo e as fontes.

Nao ha LLM nem embeddings: o vocabulario das perguntas-ouro e previsivel e casa
com os aliases declarados na ingestao.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from .graph import KnowledgeGraph


@dataclass
class Retrieval:
    seeds: list[str]
    subgraph: list[str]
    context: str
    sources: list[str]  # docs de origem (rastreabilidade)
    cenario: str = "S1"
    hypothetical_revb: bool = False
    facts: list[dict] = field(default_factory=list)


def _norm(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _detect_cenario(qn: str) -> str:
    """S2 so se a pergunta o cita explicitamente; senao S1 (padrao do corpus)."""
    if "s2" in qn or "fpso" in qn:
        return "S2"
    return "S1"


def _detect_revb(qn: str) -> bool:
    """Pergunta hipotetica sobre a revisao proposta (relaxa o filtro de vigencia)."""
    return "rev b" in qn or "revisao" in qn or ("10" in qn and "aprovad" in qn)


def _find_seeds(kg: KnowledgeGraph, qn: str, cenario: str) -> list[str]:
    """Casa os aliases de cada no contra a pergunta normalizada.

    Ordena por comprimento do alias (matches mais especificos primeiro) e restringe
    ao cenario detectado. Devolve os nos cujo alias aparece na pergunta.
    """
    hits: list[tuple[int, str]] = []
    for node_id, attrs in kg.g.nodes(data=True):
        node_cen = attrs.get("cenario")
        if node_cen is not None and node_cen != cenario:
            continue
        for alias in attrs.get("aliases", []):
            if _norm(alias) in qn:
                hits.append((len(alias), node_id))
                break
    hits.sort(reverse=True)
    return [nid for _, nid in hits]


def retrieve(kg: KnowledgeGraph, question: str, max_hops: int = 3) -> Retrieval:
    qn = _norm(question)
    cenario = _detect_cenario(qn)
    revb = _detect_revb(qn)

    seeds = _find_seeds(kg, qn, cenario)

    # Poda: mantem apenas nos do cenario detectado; por padrao exclui a decisao
    # proposta (nao vigente), salvo quando a pergunta e hipotetica sobre a Rev B.
    def keep(node_id: str, attrs: dict) -> bool:
        node_cen = attrs.get("cenario")
        if node_cen is not None and node_cen != cenario:
            return False
        status = attrs.get("status")
        if status == "proposta" and not revb:
            return False
        return True

    # Se a pergunta e sobre a Rev B, ela entra como semente adicional.
    if revb:
        for nid, attrs in kg.g.nodes(data=True):
            if attrs.get("rev") == "B" and nid not in seeds:
                seeds.append(nid)

    subgraph = kg.bfs(seeds, max_hops=max_hops, keep=keep) if seeds else []
    sources = kg.docs_of(subgraph)

    facts = []
    lines = []
    for nid in subgraph:
        attrs = kg.g.nodes[nid]
        desc = attrs.get("descricao") or attrs.get("nome") or nid
        doc = attrs.get("doc", "?")
        facts.append({"id": nid, "ntype": attrs.get("ntype"), "desc": desc, "doc": doc})
        lines.append(f"- [{nid}] {desc} (doc {doc})")

    context = "\n".join(lines)
    return Retrieval(
        seeds=seeds,
        subgraph=subgraph,
        context=context,
        sources=sources,
        cenario=cenario,
        hypothetical_revb=revb,
        facts=facts,
    )
