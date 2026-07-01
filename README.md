# GraphRAG Offshore — Desafio DSS (template)

Esqueleto inicial. **Forke este repositório**, preencha a `SPEC.md` primeiro e
implemente o agente. Veja o enunciado completo em `CHALLENGE_BRIEF` (enviado à parte).

## Estrutura
```
repo/
├── SPEC.md                 # preencha ANTES de codar
├── data/
│   ├── corpus/             # 10 documentos do estudo Açu-Deep (inclui distratores e uma revisão) (fictício)
│   └── questions.yaml      # 6 perguntas-ouro (multi-hop + armadilhas)
├── src/graphrag/
│   ├── ingest.py           # corpus -> grafo  (TODO)
│   ├── graph.py            # estrutura/consulta do grafo  (TODO)
│   ├── retrieve.py         # GraphRAG: pergunta -> subgrafo -> contexto  (TODO)
│   ├── agent.py            # orquestra retrieve + geração da resposta  (TODO)
│   └── __main__.py         # CLI: python -m graphrag "pergunta"
└── tests/
    └── test_graphrag.py    # alguns testes para você completar
```

## Como rodar (preencha conforme implementar)
```bash
pip install -r requirements.txt
# responder uma pergunta:
python -m graphrag "Por que o Cenário S1 exige aquecimento ativo?"
# rodar contra todas as perguntas-ouro:
python -m graphrag --eval data/questions.yaml
```

## Decisões de arquitetura e trade-offs
_(preencha: por que este schema, como o GraphRAG resolve multi-hop, o que cortou,
como escalaria.)_

## O que ficou de fora
_(seja honesto — isto conta a favor.)_
