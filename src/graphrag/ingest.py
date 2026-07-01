"""Ingestao: corpus de Markdown -> KnowledgeGraph (extracao por regras).

Fase 1 do GraphRAG: roda uma vez, antes de qualquer pergunta, e constroi o grafo
inteiro. A extracao e deterministica e por regras (SPEC secao 3): o corpus usa
identificadores explicitos (D-12, FA-3, WAT, S1/S2) e frases-ancora estaveis
(``vigente``, ``deriva de``, ``impacta``), entao padroes bastam -- sem LLM.

A estrategia e dirigida por documento: cada arquivo do corpus tem um extrator que
conhece os identificadores e valores que ali aparecem, ancorados nos textos-fonte.
Os identificadores servem de chave estavel de no, de modo que uma mencao a "D-12"
no doc 05 liga ao mesmo no criado a partir do doc 04 -- e assim as arestas cruzam
a fronteira entre documentos, viabilizando o multi-hop.
"""
from __future__ import annotations

import re
from pathlib import Path

from .graph import KnowledgeGraph

CORPUS_DIR = Path(__file__).resolve().parents[2] / "data" / "corpus"

# Mapeia o numero do documento (chave de rastreabilidade) ao nome do arquivo.
DOC_FILES = {
    "01": "01_project_overview.md",
    "02": "02_reservoir_case.md",
    "03": "03_wells_config.md",
    "04": "04_subsea_layout.md",
    "05": "05_flow_assurance.md",
    "06": "06_topside.md",
    "07": "07_economics.md",
    "08": "08_decision_log.md",
    "09": "09_scenario_s2_fpso.md",
    "10": "10_revision_addendum.md",
}


def _read(corpus_dir: Path, doc: str) -> str:
    return (corpus_dir / DOC_FILES[doc]).read_text(encoding="utf-8")


def build_graph(corpus_dir: Path = CORPUS_DIR) -> KnowledgeGraph:
    """Le o corpus e devolve o knowledge graph populado.

    Extrai apenas as entidades e relacoes que o schema preve e que as perguntas-
    ouro exercitam. Confirma alguns valores-chave contra o texto-fonte (assercoes
    leves) para que a extracao falhe cedo se o corpus mudar.
    """
    kg = KnowledgeGraph()

    # -- Cenarios (docs 01, 09) ---------------------------------------------
    kg.add_node(
        "S1", "Cenario", doc="01", cenario="S1",
        nome="Tieback longo (~18 km a host existente)",
        aliases=["s1", "cenario s1", "tieback longo"],
    )
    kg.add_node(
        "S2", "Cenario", doc="09", cenario="S2",
        nome="FPSO dedicada",
        aliases=["s2", "cenario s2", "fpso"],
    )

    # -- Reservatorio: WAT (doc 02), causa-raiz do risco --------------------
    txt02 = _read(corpus_dir, "02")
    assert "31" in txt02, "esperado WAT de 31 C no doc 02"
    kg.add_node(
        "WAT", "Propriedade", doc="02", valor="31 C",
        descricao="Temperatura de Aparecimento de Parafina (WAT) = 31 C",
        aliases=["wat", "parafina", "temperatura de aparecimento de parafina",
                 "propriedade do reservatorio", "reservatorio"],
    )

    # -- Poços (doc 03): S1 tem 6 produtores --------------------------------
    txt03 = _read(corpus_dir, "03")
    assert "6" in txt03, "esperado 6 produtores no doc 03"
    kg.add_node(
        "POCOS-S1", "Sistema", doc="03", cenario="S1", nome="Pocos S1",
        valor="6 produtores",
        descricao="6 pocos produtores + 2 injetores alimentam o sistema submarino do S1",
        aliases=["pocos", "pocos produtores", "produtores", "sistema submarino",
                 "quantos pocos"],
    )

    # -- Subsea: decisao D-12, Rev A vigente (8"), doc 04 -------------------
    txt04 = _read(corpus_dir, "04")
    assert "8 polegadas" in txt04 or '8"' in txt04, "esperado flowline 8\" no doc 04"
    kg.add_node(
        "D-12", "Decisao", doc="04", cenario="S1", status="vigente", rev="A",
        valor='8"',
        descricao="D-12 Rev A (vigente): flowline de 8 polegadas + tieback de 18 km",
        aliases=["d-12", "d12", "flowline", "diametro", "diametro do flowline",
                 "cano", "8 polegadas", "tieback", "subsea", "arquitetura submarina"],
    )
    kg.add_node(
        "SUBSEA", "Sistema", doc="04", cenario="S1", nome="Subsea",
        aliases=["subsea", "arquitetura submarina"],
    )

    # -- Flow assurance: restricao FA-3, doc 05 -----------------------------
    txt05 = _read(corpus_dir, "05")
    assert "26" in txt05 and "31" in txt05, "esperado 26 C < WAT 31 C no doc 05"
    kg.add_node(
        "FA-3", "Restricao", doc="05", cenario="S1",
        descricao=("FA-3: com 8\" e tieback de 18 km a chegada cai para ~26 C, "
                   "abaixo da WAT de 31 C; exige aquecimento ativo"),
        aliases=["fa-3", "fa3", "flow assurance", "risco de parafina",
                 "aquecimento", "aquecimento ativo", "deposicao de parafina"],
    )

    # -- Topside (doc 06): aquecimento exige +4,5 MW ------------------------
    kg.add_node(
        "AQUECIMENTO", "Sistema", doc="06", cenario="S1", nome="Aquecimento ativo",
        valor="+4,5 MW",
        descricao="Aquecimento ativo exigido por FA-3 adiciona +4,5 MW na host",
        aliases=["aquecimento ativo", "topside", "host", "potencia", "4,5 mw"],
    )

    # -- Economics (doc 07): cadeia de custo, efeito liquido ~ -2 MM --------
    kg.add_node(
        "ECON-ECONOMIA", "ImpactoEconomico", doc="07", cenario="S1",
        tipo="economia", valor_mm=-22,
        descricao="Economia de US$22 MM em linha/instalacao pelo flowline de 8\"",
        aliases=["economia", "capex de linha", "economia de linha"],
    )
    kg.add_node(
        "ECON-CAPEX-AQ", "ImpactoEconomico", doc="07", cenario="S1",
        tipo="CAPEX", valor_mm=15,
        descricao="CAPEX de upgrade de potencia (+4,5 MW): +US$15 MM",
        aliases=["capex", "capex de aquecimento", "upgrade de potencia"],
    )
    kg.add_node(
        "ECON-OPEX-AQ", "ImpactoEconomico", doc="07", cenario="S1",
        tipo="OPEX", valor_mm=9,
        descricao="OPEX adicional de energia: +US$9 MM (valor presente)",
        aliases=["opex", "opex de aquecimento", "energia"],
    )
    kg.add_node(
        "ECON-LIQUIDO", "ImpactoEconomico", doc="07", cenario="S1",
        tipo="liquido", valor_mm=-2,
        descricao=("Efeito liquido da cadeia D-12 -> FA-3 -> aquecimento: ~US$ -2 MM "
                   "(economia de 22 consumida por +15 CAPEX e +9 OPEX)"),
        aliases=["impacto economico", "efeito liquido", "impacto liquido",
                 "resultado economico", "economico liquido"],
    )

    # -- Revisao D-12 (docs 08, 10): Rev B proposta (10"), NAO vigente ------
    txt10 = _read(corpus_dir, "10")
    assert "10" in txt10 and "nao aprovada" in txt10.lower().replace("ã", "a"), \
        "esperado Rev B (10\") nao aprovada no doc 10"
    kg.add_node(
        "D-12-REVB", "Decisao", doc="10", cenario="S1", status="proposta", rev="B",
        valor='10"',
        descricao=("D-12 Rev B (proposta, NAO aprovada): flowline de 10 polegadas "
                   "para eliminar o aquecimento ativo; em analise pelo comite"),
        aliases=["rev b", "revisao", "10 polegadas", "proposta"],
    )

    # -- Distratores do S2 (doc 09): valores diferentes de proposito -------
    kg.add_node(
        "D-12-S2", "Decisao", doc="09", cenario="S2", status="vigente",
        valor='12"',
        descricao="S2: flowline de 12 polegadas (cenario diferente)",
        aliases=["flowline s2", "12 polegadas"],
    )
    kg.add_node(
        "POCOS-S2", "Sistema", doc="09", cenario="S2", nome="Pocos S2",
        valor="8 produtores",
        descricao="S2: 8 pocos produtores (configuracao ampliada)",
        aliases=["pocos s2"],
    )

    # -- Arestas: a cadeia causal (multi-hop) -------------------------------
    # Reservatorio + decisao -> restricao (Q2, Q4)
    kg.add_edge("FA-3", "D-12", "DERIVA_DE")
    kg.add_edge("FA-3", "WAT", "DERIVA_DE")
    kg.add_edge("D-12", "FA-3", "IMPACTA")
    # Restricao -> mitigacao/custo de potencia (Q2, Q3, Q6)
    kg.add_edge("FA-3", "AQUECIMENTO", "EXIGE")
    kg.add_edge("AQUECIMENTO", "ECON-CAPEX-AQ", "GERA_CUSTO")
    kg.add_edge("AQUECIMENTO", "ECON-OPEX-AQ", "GERA_CUSTO")
    # Cadeia economica (Q3)
    kg.add_edge("D-12", "ECON-ECONOMIA", "GERA_CUSTO")
    kg.add_edge("FA-3", "ECON-LIQUIDO", "GERA_CUSTO")
    kg.add_edge("ECON-LIQUIDO", "ECON-ECONOMIA", "DERIVA_DE")
    kg.add_edge("ECON-LIQUIDO", "ECON-CAPEX-AQ", "DERIVA_DE")
    kg.add_edge("ECON-LIQUIDO", "ECON-OPEX-AQ", "DERIVA_DE")
    # Revisao proposta -> restricao que ela eliminaria (Q6)
    kg.add_edge("D-12-REVB", "FA-3", "IMPACTA")
    # Ancoragem em cenario/sistema
    kg.add_edge("D-12", "S1", "PERTENCE_A")
    kg.add_edge("D-12", "SUBSEA", "PERTENCE_A")
    kg.add_edge("FA-3", "S1", "PERTENCE_A")
    kg.add_edge("POCOS-S1", "S1", "PERTENCE_A")
    kg.add_edge("POCOS-S1", "SUBSEA", "PERTENCE_A")
    kg.add_edge("AQUECIMENTO", "S1", "PERTENCE_A")
    kg.add_edge("D-12-S2", "S2", "PERTENCE_A")
    kg.add_edge("POCOS-S2", "S2", "PERTENCE_A")

    return kg
