"""Testes iniciais — complete-os e adicione os seus.

A ideia não é cobertura exaustiva, mas mostrar que você testa o que importa:
o grafo é construído? a recuperação faz o multi-hop esperado? as fontes
são rastreáveis?
"""
import pytest
from graphrag.ingest import build_graph


@pytest.mark.skip(reason="implemente build_graph primeiro")
def test_graph_builds():
    kg = build_graph()
    assert kg.g.number_of_nodes() > 0


@pytest.mark.skip(reason="exemplo de teste multi-hop — adapte ao seu schema")
def test_multi_hop_active_heating():
    # Q2: a resposta deve conectar WAT (reservatorio) -> D-12 (subsea) -> FA-3 (flow assurance)
    ...
