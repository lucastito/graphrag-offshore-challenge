# Plano de desenvolvimento

Fluxo spec-first, commits incrementais contando a evolução: `SPEC → teste → módulo`.
Só o necessário para atender o desafio; nada de over-engineering.

## Sequência

- [x] SPEC preenchida (schema, retrieval, avaliação, escala) — commit
- [x] Testes de aceitação (TDD, vermelhos) + config pytest/src — commit
- [x] `graph.py` — KnowledgeGraph tipado, validação pydantic, BFS com poda — commit
- [ ] `ingest.py` — extração por regras: 10 docs → grafo (Fase 1)
- [ ] `retrieve.py` — pergunta → nó de entrada → BFS com poda → subgrafo
- [ ] `agent.py` — subgrafo → resposta por template + fontes
- [ ] `eval.py` — precision/recall das fontes
- [ ] `__main__.py` — CLI (`pergunta`) e `--eval questions.yaml`
- [ ] README — arquitetura, decisões, trade-offs e **o que ficou de fora** (exigido)
- [ ] Suíte verde ponta a ponta (as 6 perguntas)
- [ ] Roteiro do vídeo de 5 min

## Cortes (deliberados) — detalhe na SPEC §1 e §6

UI, banco de grafo, embeddings, LLM em runtime, fine-tuning, frameworks de agente,
extrator de domínio aberto. Cada corte é o degrau mais simples que resolve no
tamanho atual; o degrau seguinte está registrado para quando o volume justificar.

## Regra anti-distrator (poda) — amarrada ponta a ponta

Spec §4 (poda por cenário/vigência) → `graph.py` BFS com predicado `keep` →
testes `test_q1` (vigência, rejeita 12") e `test_q5` (cenário, rejeita doc 09).
