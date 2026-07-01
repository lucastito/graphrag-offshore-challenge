"""Testes de aceitacao do agente GraphRAG.

Derivados do gabarito em data/questions.yaml. Nao buscam cobertura exaustiva:
verificam o que o desafio avalia -- o grafo e construido, a travessia multi-hop
conecta os documentos certos, os distratores nao entram, e as fontes sao
rastreaveis. Escritos antes da implementacao (TDD): comecam vermelhos.
"""
from __future__ import annotations

import unicodedata

import pytest

from graphrag.ingest import build_graph
from graphrag.agent import answer_question


def _norm(text: str) -> str:
    """Minusculas sem acento, para assercoes robustas sobre o texto da resposta."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


@pytest.fixture(scope="module")
def kg():
    return build_graph()


# --- Construcao do grafo ----------------------------------------------------

def test_graph_builds(kg):
    assert kg.g.number_of_nodes() > 0
    assert kg.g.number_of_edges() > 0


def test_key_nodes_exist(kg):
    """Nos-chave da cadeia causal devem existir apos a ingestao."""
    ids = set(kg.g.nodes)
    for expected in ("D-12", "FA-3", "WAT"):
        assert expected in ids, f"no esperado ausente: {expected}"


# --- Q1: vigencia (distrator de recencia) -----------------------------------

def test_q1_diametro_vigente_e_8(kg):
    ans = answer_question(kg, "Qual e o diametro de flowline VIGENTE do Cenario S1?")
    txt = _norm(ans.text)
    assert "8" in txt
    assert "12" not in txt  # 12" e do cenario S2 (distrator)
    assert "04" in ans.sources or "08" in ans.sources or "10" in ans.sources


# --- Q2: multi-hop (WAT -> D-12 -> FA-3) -------------------------------------

def test_q2_multi_hop_aquecimento(kg):
    ans = answer_question(kg, "Por que o Cenario S1 exige aquecimento ativo?")
    # conecta reservatorio (02), subsea (04) e flow assurance (05)
    for doc in ("02", "04", "05"):
        assert doc in ans.sources, f"fonte multi-hop ausente: doc {doc}"


# --- Q3: cadeia economica ----------------------------------------------------

def test_q3_impacto_liquido(kg):
    ans = answer_question(kg, "Qual e o impacto economico liquido de escolher o flowline de 8 polegadas no S1?")
    txt = _norm(ans.text)
    assert "2" in txt  # efeito liquido ~ -US$2MM
    assert "07" in ans.sources


# --- Q5: distrator de cenario (S2) ------------------------------------------

def test_q5_pocos_produtores_s1(kg):
    ans = answer_question(kg, "Quantos pocos produtores alimentam o sistema submarino do Cenario S1?")
    txt = _norm(ans.text)
    assert "6" in txt
    assert "09" not in ans.sources  # doc 09 (S2, diz 8 pocos) e o distrator


# --- Rastreabilidade ---------------------------------------------------------

def test_answers_have_sources(kg):
    ans = answer_question(kg, "Por que o Cenario S1 exige aquecimento ativo?")
    assert ans.sources, "resposta sem fontes rastreaveis"


# --- Metrica de recuperacao: precision/recall das fontes --------------------

def test_source_precision_recall_q5():
    """Q5 nao pode trazer o distrator: precision deve ser 1.0 nas fontes."""
    from graphrag.eval import source_precision_recall

    p, r = source_precision_recall(retrieved=["03"], gold=["03"])
    assert p == 1.0 and r == 1.0

    # se trouxesse o doc 09 (distrator), precision cai -- flagra a armadilha
    p2, _ = source_precision_recall(retrieved=["03", "09"], gold=["03"])
    assert p2 < 1.0
