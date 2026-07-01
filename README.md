# GraphRAG Offshore — Desafio DSS

Agente em Python que ingere um corpus de engenharia offshore (estudo fictício do
campo Açu-Deep), constrói um **knowledge graph** e responde perguntas em linguagem
natural via **GraphRAG**: recuperação guiada pelo grafo, com travessia multi-hop e
citação das fontes. Sem LLM em tempo de execução — a extração e a resposta são
determinísticas.

O corpus contém armadilhas de propósito (um segundo cenário, S2, e uma revisão de
decisão não aprovada). O trabalho central é recuperar a informação **vigente e do
cenário certo**, não a mais parecida.

## Documentos do projeto

Três documentos, com papéis distintos:

- **[SPEC.md](SPEC.md)** — especificação de produto: schema do grafo, estratégia de
  recuperação, regras de aceite e avaliação. Escrita antes do código.
- **[docs/adr/](docs/adr/)** — decisões de engenharia e seus trade-offs, incluindo a
  análise de escala (ex.: [ADR 0001 — calibração de precision](docs/adr/0001-calibracao-de-precision.md)).
- **README.md** (este) — visão geral e como executar.

## Como executar

Requer Python 3.10+.

```bash
pip install -e .          # instala o pacote e as dependencias (networkx, pyyaml, pydantic)

# responder uma pergunta:
python -m graphrag "Por que o Cenario S1 exige aquecimento ativo?"

# rodar contra todas as perguntas-ouro, com precision/recall das fontes:
python -m graphrag --eval data/questions.yaml

# testes:
pytest
```

No Windows, use o PowerShell para os comandos acima.

## Arquitetura

O fluxo tem duas fases separadas no tempo. A **ingestão** roda uma vez e constrói o
grafo inteiro, antes de qualquer pergunta. A **consulta** apenas entra no grafo já
pronto e percorre o subgrafo relevante.

```
FASE 1 (ingestao)   corpus (.md) --regras--> knowledge graph (networkx, em memoria)

FASE 2 (consulta)   pergunta --keyword--> no de entrada --BFS+poda--> subgrafo
                             --> resposta (template) + fontes
```

Módulos (`src/graphrag/`):

| Módulo | Papel |
|---|---|
| `graph.py` | Estrutura do grafo (schema tipado, validação `pydantic`, travessia BFS com poda) |
| `ingest.py` | Extração por regras: lê os 10 documentos e popula o grafo (Fase 1) |
| `retrieve.py` | Pergunta → nó de entrada por keyword → BFS com poda → subgrafo (Fase 2) |
| `agent.py` | Subgrafo → resposta por template determinístico + fontes |
| `eval.py` | Precision/recall das fontes contra o gabarito |
| `__main__.py` | CLI (`pergunta` e `--eval`) |

## Como o GraphRAG resolve o multi-hop e as armadilhas

As entidades levam identificadores estáveis (`D-12`, `FA-3`, `WAT`), então uma
menção a `D-12` num documento liga ao mesmo nó criado em outro — é isso que permite
a travessia cruzar documentos. A cadeia causal
`WAT → D-12 → FA-3 → aquecimento → custo` responde às perguntas multi-hop mesmo
quando os documentos de origem não compartilham vocabulário.

Cada nó carrega `cenario` (S1/S2) e `status` (vigente/proposta). A travessia **poda**
o que não pertence ao cenário detectado ou o que não está vigente (exceto quando a
pergunta é explicitamente hipotética sobre a revisão). É assim que o distrator do S2
e a Rev B não contaminam as respostas.

## Resultados

`--eval` sobre as seis perguntas-ouro: **precision média 0.76, recall médio 0.94**,
com **nenhum distrator do S2 recuperado** em qualquer pergunta (o modo de falha que o
desafio testa). A Q5 fica em 1.00/1.00. O raciocínio da calibração de precision e sua
validade em escala estão no [ADR 0001](docs/adr/0001-calibracao-de-precision.md).

## O que ficou de fora (deliberado)

O escopo do desafio é maior do que cabe no tempo previsto; a opção foi entregar uma
fatia vertical que funciona ponta a ponta. Cortes conscientes:

- **Interface gráfica** — a entrega é por CLI.
- **Banco de grafo (Neo4j)** — `networkx` em memória basta para 10 documentos.
- **Busca por embeddings** — o vocabulário das perguntas é previsível; keyword resolve.
- **LLM em runtime e fine-tuning** — extração e resposta são determinísticas e rodam
  sem chave.
- **Frameworks de agente (LangChain, CrewAI, LangGraph)** — o motor é travessia
  determinística; um framework de orquestração de LLM seria peso morto e reduziria a
  explicabilidade.
- **Extrator de domínio aberto** — o extrator é sob medida para este corpus.

Como cada corte mudaria em escala (~10.000 documentos) está detalhado na
[SPEC](SPEC.md) (seção 1.1 e 6) e nos ADRs: em resumo, ontologia definida com
especialistas, extração por LLM guiada por ela, entrada por embeddings e geração por
LLM avaliada com RAGAS e holdout.
