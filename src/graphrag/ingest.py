"""Ingestão: corpus de Markdown -> KnowledgeGraph.

TODO:
- Ler data/corpus/*.md
- Extrair entidades e relações (LLM / regras / híbrido — justifique na SPEC)
- Popular o KnowledgeGraph
- Garantir um modo SEM chave de LLM (fallback) OU documentar execução.
"""
from __future__ import annotations
from pathlib import Path
from .graph import KnowledgeGraph

CORPUS_DIR = Path(__file__).resolve().parents[2] / "data" / "corpus"


def build_graph(corpus_dir: Path = CORPUS_DIR) -> KnowledgeGraph:
    kg = KnowledgeGraph()
    # TODO: implementar
    raise NotImplementedError
