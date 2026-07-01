# ADR 0001 — Calibração de precision na recuperação

- **Status:** aceito
- **Contexto:** decisão de engenharia, tomada após os testes de aceitação passarem
  (8/8), ao observar as métricas de recuperação.

## Contexto

Com a travessia inicial (BFS até 3 hops por todas as arestas), a suíte de aceitação
já passava, mas o `--eval` mostrava **recall médio 0.94 e precision média 0.53**. O
recall alto indica que o grafo conecta bem — a partir de qualquer nó, a travessia
alcança as fontes corretas. A precision baixa indica o oposto: alcançava as corretas
junto com muitas irrelevantes. O grafo é pequeno e denso, então expandir três saltos
de qualquer nó chega a quase tudo.

Neste corpus a métrica prioritária é **precision**, não recall. As armadilhas do
desafio — o documento do cenário S2 e a revisão não aprovada (Rev B) — são falsos
positivos à espera de quem recupera o material mais parecido. Trazer o distrator é o
modo de falha que o desafio testa; é um erro de precision. Recall importa, mas perder
uma fonte é menos grave aqui do que contaminar a resposta com o documento errado.

## Decisão

Duas mudanças de princípio na travessia (não ajustes caso a caso para bater o
gabarito):

1. **Nós organizacionais não são ponto de entrada.** Os nós de tipo `Cenario` (S1/S2)
   e o nó de disciplina `Subsea` foram removidos do conjunto de sementes. O cenário
   já é detectado à parte e usado como filtro; esses nós apenas agrupam e, por serem
   muito conectados, arrastavam a cadeia inteira para dentro do subgrafo.

2. **Arestas de custo só são seguidas em perguntas de custo.** As arestas
   `GERA_CUSTO` (que levam aos nós de `ImpactoEconomico`) só entram na travessia
   quando a pergunta é econômica. Em perguntas não financeiras, a cadeia de custo
   (topside, economics) é ruído.

Também se manteve a travessia restrita às arestas causais (`IMPACTA`, `DERIVA_DE`,
`EXIGE`), deixando `PERTENCE_A` fora da expansão, e a profundidade adaptativa (1 hop
para perguntas diretas, 2 para multi-hop).

## Consequência

Precision média subiu de **0.53 → 0.76** com recall mantido em **0.94**. A Q5
(single-hop com distrator) chegou a 1.00/1.00. Nenhum distrator do S2 é recuperado
em qualquer pergunta. O recall abaixo de 1.0 vem da Q1, que não recupera o log de
decisões (doc 08) por ele não ser modelado como nó próprio.

**Onde paramos e por quê.** Perseguir cada documento residual exigiria regras cada
vez mais específicas às seis perguntas — sobreajuste ao gabarito, frágil e contrário
ao objetivo de recuperação explicável. A recuperação seletiva já está demonstrada;
o retorno de continuar é decrescente.

## Estas escolhas escalam?

Análise honesta do que sobrevive a ~10.000 documentos e do que não.

- **Nós organizacionais fora das sementes — escala, com outra forma.** A distinção
  entre nó-âncora (organiza) e nó-conteúdo (responde) é válida em qualquer tamanho,
  mas listá-los à mão (como `Subsea` aqui) não. Em escala isso vira **propriedade da
  ontologia**: cada tipo de nó declara se é âncora ou conteúdo, e a regra deixa de ser
  local para ser do schema.

- **Arestas de custo por palavra-chave — a ideia escala, a implementação não.**
  Ativar sub-grafos conforme a intenção da pergunta é uma boa estratégia em qualquer
  escala. Mas detectá-la por palavra-chave (`custo`, `impacto`) quebra com linguagem
  livre — "vale a pena o cano fino?" não contém a palavra "custo". A versão que escala
  **classifica a intenção da pergunta** (roteador ou embedding) e ativa os tipos de
  aresta conforme a intenção, em vez de casar strings.

- **Uma ontologia mais rica reduziria o próprio problema.** Parte da precision baixa
  foi sintoma de ontologia pobre, não só de travessia larga. Com hierarquia de
  relações e cardinalidade declaradas, a travessia guiada por tipo seria nativa e boa
  parte desta calibração manual seria desnecessária. Foi uma troca consciente:
  investir em poda agora custou menos tempo do que formalizar uma ontologia completa,
  adequada ao tamanho do problema — mas em escala a ontologia é o caminho que dá
  precision por construção, e não por ajuste posterior.

## Alternativas consideradas

- **Elevar recall a 1.0 modelando o doc 08 como nó** e perseguindo os documentos
  residuais: descartado por sobreajuste ao gabarito e retorno decrescente.
- **Manter a travessia larga e filtrar o subgrafo depois** (re-ranking): mais
  complexo, sem ganho claro neste tamanho de corpus.
