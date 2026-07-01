# SPEC — GraphRAG sobre dados de engenharia offshore

> Preencha esta especificação **antes** de escrever código. Ela deve guiar a
> implementação. Seja conciso; bullets servem. Mantenha-a coerente com o que você
> realmente construir (atualize se mudar de ideia, mas registre o porquê).

## 1. Objetivo e escopo
- O que este agente faz (1–2 frases):
- O que está **explicitamente fora** de escopo nesta entrega:

## 2. Schema do knowledge graph
### Tipos de nó
| Tipo de nó | O que representa | Atributos-chave | Por quê |
|---|---|---|---|
|  |  |  |  |

### Tipos de aresta (relações)
| Tipo de aresta | De → Para | Direcionada? | Por quê |
|---|---|---|---|
|  |  |  |  |

- Por que este schema permite responder perguntas multi-hop:

## 3. Ingestão / extração
- Estratégia (LLM / regras / híbrido) e justificativa:
- Como você lida com referências entre documentos (ex.: "decisão D-12"):
- Modo de execução sem chave de LLM (fallback) — descreva:

## 4. Estratégia de recuperação (GraphRAG)
- Como você escolhe o(s) nó(s) de entrada a partir da pergunta:
- Como faz a travessia (BFS/DFS, profundidade, filtros por tipo de aresta):
- Como monta o contexto e gera a resposta final:
- Como garante rastreabilidade (citação de fontes):

## 5. Avaliação
- Como você sabe que uma resposta está correta:
- O que você testa (e o que deliberadamente não testa):

## 6. Trade-offs e cortes
- O que cortou por causa do tempo:
- O que faria com mais tempo / como escalaria para 10.000 documentos:
