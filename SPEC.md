# SPEC — GraphRAG sobre dados de engenharia offshore

Especificação escrita antes do código. Define o schema do grafo, a estratégia de
recuperação e a forma de avaliação, e registra as escolhas de engenharia com seus
trade-offs. Cada seção diz o que foi escolhido para esta entrega e o que mudaria em
escala (a ordem de grandeza que o desafio pede para considerar: ~10.000 documentos).

## 1. Objetivo e escopo

- **O que este agente faz:** dada uma pergunta em linguagem natural sobre o estudo
  de concepção do campo Açu-Deep, o agente recupera o subgrafo relevante de um
  knowledge graph construído a partir do corpus, percorre a cadeia multi-hop
  necessária e devolve uma resposta ancorada nas evidências, citando os documentos
  de origem.

- **O que está explicitamente fora de escopo nesta entrega:**
  - Interface gráfica. A entrega é por CLI (`python -m graphrag`).
  - Banco de grafo externo. O grafo vive em memória com `networkx`.
  - Busca semântica por embeddings. O ponto de entrada é por palavra-chave.
  - Extração por LLM em tempo de execução e fine-tuning.
  - Cobertura de perguntas fora das seis perguntas-ouro. O extrator é sob medida
    para o vocabulário deste corpus, não um extrator de domínio aberto.

O escopo do desafio é maior do que cabe no tempo previsto. A opção aqui é entregar
uma fatia vertical estreita que funciona ponta a ponta — ingestão, grafo,
recuperação, resposta, avaliação — em vez de vários módulos parciais. Os cortes
acima são deliberados e estão detalhados nas seções seguintes.

**Em escala** o recorte de escopo muda pouco: continuaria sem UI e com CLI/serviço,
mas embeddings, banco de grafo e possivelmente LLM na geração deixariam de ser
cortes e passariam a ser requisitos (seções 3 a 5).

## 2. Schema do knowledge graph

### Tipos de nó

| Tipo de nó | O que representa | Atributos-chave | Por quê |
|---|---|---|---|
| `Cenario` | Uma concepção de desenvolvimento (S1, S2) | `id`, `nome`, `doc` | Separa o cenário em foco (S1) do distrator (S2) |
| `Decisao` | Uma decisão de engenharia, possivelmente revisada | `id`, `valor`, `status`, `rev`, `cenario`, `doc` | Distingue a revisão vigente da proposta (Rev A vs Rev B) |
| `Restricao` | Uma restrição de engenharia (risco de parafina) | `id`, `descricao`, `cenario`, `doc` | É o elo causal entre a decisão de subsea e o custo |
| `Propriedade` | Propriedade física do reservatório (WAT) | `id`, `valor`, `doc` | É a causa-raiz do risco de flow assurance |
| `Sistema` | Um subsistema ou disciplina (Subsea, Topside, Poços) | `id`, `nome`, `cenario`, `doc` | Agrupa entidades e indica a disciplina de origem |
| `ImpactoEconomico` | Um efeito de custo ou economia quantificado | `id`, `valor_mm`, `tipo`, `cenario`, `doc` | Fecha a cadeia decisão → restrição → resultado financeiro |

São seis tipos, dentro da faixa de 4 a 6 sugerida pelo desafio. Cada tipo existe
porque aparece em ao menos uma das perguntas-ouro; nada foi modelado por
completude. Os atributos `status` (vigente/proposta) e `cenario` (S1/S2) carregam a
informação que separa a fonte correta da fonte apenas parecida — são eles que a
recuperação usa para descartar os distratores.

### Tipos de aresta (relações)

| Tipo de aresta | De → Para | Direcionada? | Por quê |
|---|---|---|---|
| `IMPACTA` | `Decisao` → `Restricao` | sim | O cano de 8" impacta o comportamento térmico (D-12 → FA-3) |
| `DERIVA_DE` | `Restricao` → `Decisao` / `Propriedade` | sim | FA-3 deriva de D-12 e da WAT — a espinha da cadeia multi-hop |
| `EXIGE` | `Restricao` → `Sistema` / `ImpactoEconomico` | sim | FA-3 exige aquecimento ativo (+4,5 MW e custo associado) |
| `GERA_CUSTO` | `Decisao` / `Restricao` → `ImpactoEconomico` | sim | Liga a cadeia técnica ao efeito financeiro (Q3, Q6) |
| `PERTENCE_A` | qualquer nó → `Cenario` / `Sistema` | sim | Ancora cada entidade no seu cenário e disciplina |

- **Por que este schema permite responder perguntas multi-hop:** as arestas
  `IMPACTA`, `DERIVA_DE`, `EXIGE` e `GERA_CUSTO` formam a cadeia
  `Propriedade(WAT) → Decisao(D-12) → Restricao(FA-3) → ImpactoEconomico`. Uma
  pergunta que entra por qualquer ponto dessa cadeia alcança os demais seguindo as
  arestas, mesmo quando os documentos de origem não compartilham vocabulário. As
  arestas são tipadas para permitir travessia dirigida — seguir apenas o elo causal
  relevante — em vez de expandir por qualquer vizinho.

**Em escala** o schema deixa de ser modelado à mão e passa a derivar de uma
ontologia definida com especialistas de domínio a partir de uma amostra do corpus,
não da leitura integral. A estrutura de nós e arestas permanece; o que muda é a
origem do schema e o volume de tipos.

## 3. Ingestão / extração

- **Estratégia: extração por regras determinísticas, sem LLM.** O corpus é pequeno
  e estruturado: os identificadores são explícitos (`D-12`, `FA-3`, `A-07`, `E-04`,
  `Rev A/B`, `S1/S2`) e as relações aparecem em frases-âncora estáveis (`vigente`,
  `deriva de`, `impacta`, `requer aquecimento`). Isso torna a extração por padrões
  suficiente e traz três propriedades que o desafio pede: determinismo (o grafo é
  idêntico a cada execução, o que sustenta testes de aceitação exatos), execução sem
  chave de LLM e explicabilidade completa (é possível justificar cada nó e aresta).

- **Como lidamos com referências entre documentos:** os identificadores servem de
  chave estável de nó. Quando o documento de Flow Assurance menciona "decisão D-12",
  o extrator liga ao mesmo nó `D-12` já criado a partir do documento de Subsea. É
  assim que as arestas cruzam a fronteira entre documentos e o multi-hop se torna
  possível.

- **Modo de execução sem chave de LLM:** é o modo padrão e único necessário. A
  geração da resposta usa templates (seção 4). Um modo opcional com LLM pode ser
  plugado atrás de variável de ambiente sem alterar grafo nem recuperação.

- **Bibliotecas:** `networkx` para o grafo em memória e `pydantic` para validar a
  forma dos nós e arestas contra o schema antes de inseri-los. Não usamos framework
  de orquestração de agentes (LangChain, LlamaIndex, CrewAI, LangGraph, AutoGen): o
  motor deste agente é travessia determinística, não uma cadeia de chamadas a LLM;
  um framework desses seria peso morto e reduziria a explicabilidade. Não usamos
  cliente de LLM na ingestão pelos mesmos motivos de determinismo e custo.

O trade-off assumido é que a extração por regras é sob medida para este corpus e
não generaliza para documentos com vocabulário imprevisível. É uma troca consciente
de generalidade por determinismo, adequada ao tamanho do problema.

**Em escala** a extração por regras não se sustenta. O caminho seria um LLM
extraindo entidades e relações guiado pela ontologia da seção 2 — preenchendo um
schema já definido, não operando livremente sobre o texto — com validação por
`pydantic` para preservar determinismo onde importa. Jogar o corpus inteiro no
contexto de um LLM e esperar que ele se organize sozinho não é recuperação e está
descartado.

## 4. Estratégia de recuperação (GraphRAG)

- **Escolha do nó de entrada:** keyword matching contra apelidos declarados em cada
  nó. A pergunta é normalizada (minúsculas, sem acento) e casada com os aliases
  ("flowline", "diâmetro", "8 polegadas" → `D-12`; "poços produtores" → nó de poços;
  "aquecimento" → `FA-3`). O vocabulário das perguntas é previsível o bastante para
  dispensar busca semântica.

- **Detecção de cenário e de vigência:** se a pergunta cita S2 explicitamente, o
  filtro passa a `cenario == S2`; caso contrário o padrão é S1, como o corpus
  determina. Por padrão a travessia considera apenas nós com `status == vigente`.
  Quando a pergunta é hipotética sobre a revisão ("se a Rev B fosse aprovada"), o
  filtro de status é relaxado para incluir a decisão proposta e a cadeia é
  recalculada sobre ela.

- **Travessia:** BFS a partir dos nós de entrada, profundidade de até 3 hops,
  seguindo as arestas tipadas da cadeia causal (`IMPACTA`, `DERIVA_DE`, `EXIGE`,
  `GERA_CUSTO`, `PERTENCE_A`). Nós que não passam no filtro de cenário ou status são
  podados e não entram no subgrafo. Escolhemos BFS por profundidade limitada porque
  o interesse é o que está próximo na cadeia causal, não caminhos longos; DFS não
  traria vantagem e complicaria o controle de profundidade.

- **Contexto e resposta:** o subgrafo recuperado é serializado em contexto textual
  com proveniência (cada fato carrega seu documento de origem). A resposta é gerada
  por template por tipo de pergunta — valor mais a explicação da cadeia mais as
  fontes. O modo LLM opcional substituiria o template usando o mesmo contexto
  recuperado, sem alterar a recuperação.

- **Rastreabilidade:** cada nó guarda seu documento de origem; a recuperação devolve
  a lista de documentos dos nós usados, e a resposta final imprime essas fontes.
  Nenhum documento é citado sem ter entrado no subgrafo.

O filtro de cenário e vigência dentro da travessia é o que faz o agente responder
"8 polegadas" (vigente) em vez de "10" (proposta) ou "12" (cenário S2). Um RAG por
embeddings traria os três porque os três se parecem com a resposta; aqui a
recuperação é seletiva e o critério de poda é auditável.

**Em escala** o ponto de entrada por keyword deixa de funcionar, porque pergunta e
nó passam a usar palavras diferentes para o mesmo conceito. O caminho é embeddings
pré-calculados por nó na ingestão e comparados com o embedding da pergunta para
localizar os nós de entrada. A travessia permanece igual — embeddings localizam a
porta, o grafo faz o raciocínio multi-hop. Em ambos os casos o grafo é construído
inteiro na ingestão, antes de qualquer pergunta; a consulta apenas entra e percorre.

## 5. Avaliação

- **Como sabemos que uma resposta está correta:** cada pergunta-ouro traz no
  `questions.yaml` os documentos-fonte e os fatos esperados. O teste de aceitação
  verifica dois níveis: as fontes recuperadas contêm as esperadas e não contêm os
  distratores (Q5 não pode citar o documento do S2), e a resposta contém o valor
  correto (Q1 contém "8", não "10" nem "12").

- **Métrica de recuperação: precision e recall sobre as fontes.** Para cada pergunta
  comparamos os documentos recuperados com os documentos-ouro. Recall mede quanto da
  evidência correta foi recuperado; precision mede quanto do que foi recuperado era
  correto. O modo `--eval` reporta os dois. A prioridade é precision: as armadilhas
  do corpus — o documento do S2 e a Rev B não aprovada — são falsos positivos à
  espera de quem recupera o mais parecido, e trazê-los derruba a precision. Perder
  uma fonte correta é falso negativo e afeta o recall; também é indesejável, mas não
  é o modo de falha que o desafio testa em primeiro lugar.

- **O que testamos:** que o grafo é construído e contém os nós esperados; que a
  travessia da Q2 conecta WAT → D-12 → FA-3; que os filtros anti-distrator funcionam
  (vigência na Q1, cenário na Q5); e que a cadeia econômica da Q3 chega ao efeito
  líquido.

- **Resultado medido (`--eval`):** precision média 0.76 e recall médio 0.94 das
  fontes, com **nenhum distrator do S2 recuperado em qualquer pergunta** — que é o
  modo de falha central do desafio. A Q5 (single-hop com distrator) fica em 1.00/1.00.
  O recall abaixo de 1.0 vem da Q1, que não recupera o log de decisões (doc 08) por
  ele não ser modelado como nó próprio; a decisão foi não perseguir cada documento
  residual para evitar sobreajuste ao gabarito — a recuperação seletiva já está
  demonstrada.

- **O que deliberadamente não testamos:** fluência do texto gerado, perguntas fora
  do conjunto-ouro e robustez a variações linguísticas amplas — o entity linking é
  sob medida para este corpus.

Não usamos as métricas do RAGAS (faithfulness, answer relevancy e afins) porque elas
medem erro de geração por LLM. Como a resposta vem de template determinístico sobre
os nós recuperados, ela é fiel por construção e não há alucinação a medir; o que
importa aqui é a qualidade da recuperação, capturada por precision e recall das
fontes. Também não usamos holdout: com apenas seis perguntas-ouro, elas formam uma
suíte de aceitação completa e não uma amostra — testamos o universo inteiro.

**Em escala** as duas escolhas se invertem. Com LLM na geração, as métricas do RAGAS
voltam a ser necessárias para medir fidelidade e relevância. E com um conjunto grande
de perguntas passa a fazer sentido separar um holdout não visto, medir precision e
recall da extração e da recuperação sobre ele e promover uma versão apenas quando
supera a anterior por uma margem definida.

## 6. Trade-offs e cortes

- **O que cortamos por causa do tempo e do tamanho do problema:**
  - UI, banco de grafo, embeddings, LLM em tempo de execução e fine-tuning.
  - Extrator genérico de domínio aberto — o nosso é sob medida para este corpus.
  - Frameworks de orquestração de agentes — desnecessários sem LLM no motor.

- **O que faríamos com mais tempo, e como escalaria para 10.000 documentos:**
  - Ontologia definida com especialistas a partir de uma amostra, substituindo o
    schema modelado à mão.
  - Extração por LLM guiada pela ontologia, validada por `pydantic`.
  - Ponto de entrada por embeddings, mantendo a travessia de grafo para o multi-hop.
  - Geração por LLM sobre o contexto recuperado, com avaliação por RAGAS e holdout.
  - Persistência em banco de grafo (por exemplo Neo4j) e índice vetorial para os nós.
  - Versionamento de decisões mais rico do que o atributo `status` usado hoje.

As decisões desta entrega seguem a mesma lógica: adotar o degrau mais simples que
resolve o problema no tamanho atual e registrar explicitamente o degrau seguinte
para quando o volume justificar o custo.
