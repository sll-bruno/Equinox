# Lagrangian Bulls / Equinox — relatório consolidado da pesquisa

**Data de corte:** 13 de agosto de 2026

**Status:** mecanismo econômico observado; estratégia ainda não validada

**Universo atual:** BTCUSDT spot e perpétuo linear da Bybit

## 1. Resumo executivo

O projeto investiga uma estratégia de *funding carry* aproximadamente neutra à direção do Bitcoin:

```text
comprar BTC spot + vender BTC perpétuo na mesma quantidade
```

Quando o funding é positivo, participantes long no perpétuo pagam participantes short. A estratégia fornece essa ponta short e usa o BTC spot para compensar, aproximadamente, as oscilações direcionais do contrato. O retorno pretendido não vem de prever se o BTC subirá ou cairá, mas de receber funding e eventualmente capturar convergência de basis, líquidos de taxas, spread, slippage e riscos de margem.

A pergunta de pesquisa consolidada é:

> Em quais regimes o funding futuro e a dinâmica do basis remuneram suficientemente uma posição long spot + short perp, depois de custos e considerando o capital necessário para manter a ponta short viva?

O primeiro piloto corrigido encontrou carry positivo, mas pequeno:

- funding recebido: **+0,6675%**;
- hedge/basis: **-0,0055%**;
- retorno bruto: **+0,6620%**;
- retorno líquido no cenário-base: **+0,2486%** sobre o nocional;
- retorno no cenário de custos estressados: **-0,1648%**.

Com buffer segregado de margem de 25%, o retorno-base foi **+0,1989% sobre o capital empregado** em aproximadamente 93 dias. Uma anualização mecânica seria perto de 0,78%, mas não é uma estimativa defensável com apenas três meses.

O resultado central é, portanto:

> O mecanismo de carry apareceu nos dados, mas ainda não há evidência de que ele seja robusto a custos, regimes de mercado e necessidade de colateral. A ideia continua como hipótese de pesquisa, não como estratégia validada.

## 2. Enquadramento para o Desafio Quant AI

Os critérios registrados do desafio são:

| Critério | Peso | Como o projeto deve responder |
|---|---:|---|
| Nome e identidade | 5% | Lagrangian Bulls como identidade coerente, sem substituir a tese |
| Conceito e criatividade | 20% | carry hedgeado como mecanismo econômico real, não previsão genérica de preço |
| Modelagem | 20% | decisão operacional explícita, dados point-in-time e política de risco |
| Backtest | 15% | custos, margem, execução em `t+1`, splits temporais e controle de vieses |
| Análise | 15% | explicar resultados positivos, negativos, riscos e condições de falha |
| Conclusão e próximos passos | 10% | critérios objetivos para avançar, simplificar ou abandonar a tese |
| Uso de GenAI | 15% | uso rastreável em pesquisa, revisão metodológica, código e análise |

A força narrativa da proposta não é “usar HMM em cripto”. É transferir a lógica institucional de captura de prêmio/carry para um mercado de perpétuos grande e líquido, modelando explicitamente os riscos que tornam o aparente arbitrage imperfeito.

O diferencial defensável deve ser:

1. mecanismo econômico claro;
2. contabilidade reproduzível;
3. política realista de margem e custos;
4. identificação de regimes somente se ela melhorar um baseline simples fora da amostra.

## 3. Perpétuos, funding e participantes — explicação intuitiva

Um futuro perpétuo acompanha o preço do BTC, mas não entrega Bitcoin e não possui vencimento. O preço de entrada é apenas a referência para calcular lucro e prejuízo.

Exemplo: BTC está em US$ 100 mil. Bruno abre um long de 1 BTC perp e Schade abre um short de 1 BTC perp. Se o preço sobe para US$ 105 mil:

- Bruno ganha US$ 5 mil;
- Schade perde US$ 5 mil;
- nenhum BTC precisa ser entregue;
- a infraestrutura transfere P&L entre as margens dos participantes.

Em termos econômicos, todo long encontra um short correspondente. A exchange organiza o livro, calcula P&L, exige garantias e executa liquidações, mas não precisa ser a contraparte econômica final da operação.

O contrato pode ficar aberto indefinidamente enquanto:

- a margem atende aos requisitos;
- o operador suporta funding e demais custos;
- a exchange ou protocolo continua operando;
- nenhuma regra de risco força o encerramento.

### Funding

Como não há vencimento para obrigar o perp a convergir ao spot, o funding cria um incentivo periódico:

- funding positivo: longs pagam shorts;
- funding negativo: shorts pagam longs.

Funding positivo não significa que o BTC subirá. Ele indica qual ponta paga naquele instante. BTC pode cair com funding positivo e pode subir com funding negativo.

Para um perp linear da Bybit, o caixa recebido pelo short em um settlement positivo é:

```text
funding em USDT = quantidade de BTC × mark price × funding rate
```

## 4. Como a estratégia ganha — e como pode perder

Exemplo simplificado, sem alavancagem econômica:

- comprar 1 BTC spot por US$ 100 mil;
- abrir short de 1 BTC perp;
- receber funding de 0,01% sobre o valor marcado.

Se o BTC cai para US$ 90 mil, o spot perde aproximadamente US$ 10 mil e o short ganha aproximadamente US$ 10 mil. Se sobe para US$ 110 mil, ocorre o inverso. O funding é a remuneração buscada.

Entretanto, o hedge não elimina todos os riscos. O resultado completo é:

```text
P&L líquido = funding recebido ou pago
            + P&L do hedge/basis
            - taxas spot e perp
            - spread e slippage
            - custos de margem, financiamento e transferência
            - perdas operacionais ou de liquidação
```

O trade pode perder dinheiro quando:

- funding inverte ou deixa de compensar os custos;
- spot e perp se afastam de modo desfavorável;
- entradas e saídas frequentes acumulam taxas;
- a margem do short acaba durante uma alta forte;
- spread, slippage ou capacidade real são piores que os assumidos;
- há falha de exchange, custódia, stablecoin ou infraestrutura.

## 5. Basis

Basis é a diferença entre perp e spot:

```text
basis = preço do perp - preço spot
```

Basis alto não é automaticamente ruim. Se o perp está acima do spot, comprar spot e vender perp pode travar uma diferença favorável se houver convergência. O problema é que o perp não vence: o basis pode abrir ainda mais antes de convergir ou nunca convergir no horizonte da posição.

A decisão correta compara:

```text
funding esperado + convergência esperada do basis
versus
custos + risco de abertura do basis + margem necessária
```

## 6. Centralizado, DeFi e descentralização

A tese econômica é a mesma em CEX ou DeFi. Muda o caminho operacional e o conjunto de riscos.

| Aspecto | CEX | DEX / DeFi |
|---|---|---|
| Custódia | exchange mantém ativos e margem | carteira e smart contracts |
| Execução | livro centralizado | protocolo e liquidez on-chain |
| Riscos | contraparte, bloqueio, insolvência | smart contract, oracle, bridge e gas |
| Dados | geralmente mais simples e líquidos | transparentes on-chain, mas heterogêneos |
| Funding carry | mesma lógica econômica | mesma lógica econômica |

O atrativo de DeFi é a infraestrutura programável e auditável, não um funding magicamente superior. Para a primeira validação foi escolhida uma única venue centralizada e líquida, evitando misturar metodologias e timestamps.

## 7. Dados e recortes utilizados

O piloto principal usa Bybit BTCUSDT:

- janela: 12/05/2026 00:00 UTC a 13/08/2026 00:00 UTC;
- 2.233 observações horárias;
- 280 settlements de funding;
- spot, perp last price, mark price e funding alinhados em UTC.

Foi usada ainda uma janela histórica separada de estresse:

- janela: 01/10/2023 a 01/09/2024, exclusiva no fim;
- objetivo: testar a margem do short durante o rally de 2023–2024;
- 1.008 settlements, dos quais 95 tiveram funding negativo;
- excursão adversa do BTC superior a 170% para um short mantido desde o começo do período.

Essas janelas não formam um backtest histórico contínuo. O piloto serve para verificar mecânica e custos; o rally serve como teste específico de margem.

Os dados disponíveis ainda não cobrem de forma plenamente confiável:

- bid/ask histórico e spread efetivamente executável;
- slippage e profundidade do livro para diferentes tamanhos;
- regras históricas exatas de risk tiers e liquidação;
- open interest e liquidações com cobertura point-in-time já validada;
- custos de financiamento, custódia e transferência.

## 8. Convenções de backtest

### 8.1 Basis points

Um basis point, ou bp, equivale a 0,01%:

```text
1 bp = 0,01% = 0,0001 em decimal
```

Consequentemente:

- 0,5 bp = 0,005%;
- 10 bp = 0,10%;
- 100 bp = 1%.

Para evitar ambiguidade, thresholds de funding são descritos por settlement. Retornos agregados são apresentados em percentual e, quando útil, convertidos para bp.

### 8.2 Quantidade fixa

Cada entrada normaliza o spot para 1 USDT de nocional e fixa:

```text
q = 1 / preço spot de entrada
```

A mesma quantidade `q` é usada até a saída para:

- P&L spot;
- P&L short perp;
- funding;
- taxas;
- margem.

Para relatórios de margem, a unidade é escalada para US$ 100 de spot.

### 8.3 Point-in-time

Uma taxa liquidada em `t` pertence à posição carregada até aquele settlement. Ela pode informar uma decisão executada no próximo open horário, `t+1`. Uma posição aberta somente em `t` não recebe retroativamente o funding daquele instante.

### 8.4 Preços

- last-traded open: execução e P&L negociável;
- mark price: funding, basis e verificação de margem;
- spot open: define a quantidade de BTC comprada.

### 8.5 Custos

As taxas taker VIP 0 atualmente utilizadas são:

- spot: 0,10% do valor efetivamente negociado;
- perp: 0,055% do valor efetivamente negociado.

Elas são cobradas na entrada e na saída de cada perna. Como o preço muda, o custo do ciclo não é necessariamente exatamente 0,31%.

Três cenários foram preservados:

| Cenário | Cálculo | Interpretação |
|---|---:|---|
| Fee-only | 1,0× taxas | somente taxas documentadas |
| Base | 1,5× taxas | taxas mais proxy moderada de spread/slippage |
| Stress | 3,0× taxas | fricção adversa |

O excesso sobre 1,0× é uma proxy, não execução observada.

## 9. Erros encontrados e corrigidos

O primeiro motor misturava grandezas economicamente incompatíveis. As principais correções foram:

1. **Percentuais com denominadores diferentes:** spot e perp eram compensados por retornos percentuais, embora a posição real fosse uma quantidade fixa de BTC. Agora são somados fluxos de caixa em USDT para a mesma `q`.
2. **Funding com nocional artificialmente constante:** antes, a taxa era tratada como retorno direto de um nocional sempre igual. Agora o funding é `q × mark × taxa` em cada settlement.
3. **Quantidade inconsistente entre módulos:** performance, fees e margem podiam usar tamanhos diferentes. Agora todos usam a quantidade definida pelo spot na entrada.
4. **Preço de entrada da margem:** o short era marcado a partir do mark, que não é executável. Agora começa no last price do perp e é reavaliado pelo mark.
5. **Taxas na margem:** a fee de entrada não reduzia o colateral e a fee estimada de fechamento não entrava na necessidade de manutenção. Ambas passaram a ser consideradas.
6. **Atraso excessivo do funding no sinal:** o último settlement era atrasado por mais um intervalo de oito horas. Agora o valor liquidado em `t` pode orientar a ordem em `t+1`.
7. **Composição indevida:** fluxos de caixa normalizados eram tratados como retornos horários compostos. Agora o equity é formado pela soma cumulativa dos cashflows.
8. **Saída terminal:** uma posição ainda aberta no final agora paga explicitamente o fechamento das duas pernas.

Essas correções reduziram o retorno bruto always-on anteriormente publicado de 0,8203% para 0,6620%. A diferença não é uma piora do mercado; é a remoção de uma superestimação contábil.

## 10. Resultados do piloto

### 10.1 Always-on

| Componente | Retorno | Equivalente por US$ 100 mil de spot |
|---|---:|---:|
| Funding | +0,6675% | +US$ 667,55 |
| Hedge/basis | -0,0055% | -US$ 5,52 |
| Bruto | +0,6620% | +US$ 662,03 |
| Taxas observáveis | -0,2756% | -US$ 275,62 |
| Proxy adicional base | -0,1378% | -US$ 137,81 |
| Líquido-base | **+0,2486%** | **+US$ 248,60** |

O trade ficou exposto 99,96% do período e teve apenas dois meios-giros: entrada e fechamento terminal.

O break-even ocorre com custo total próximo de 2,40 vezes as taxas oficiais. Depois das fees, restam 38,64 bp para absorver todas as demais fricções antes de o lucro bruto desaparecer.

### 10.2 Cenários de custo

| Cenário | Retorno líquido |
|---|---:|
| Fee-only | +0,3864% |
| Base | +0,2486% |
| Stress | -0,1648% |

O resultado positivo não possui folga suficiente para afirmar robustez.

### 10.3 Regras reativas

| Regra | Bruto | Taxas oficiais | Líquido-base | Meios-giros |
|---|---:|---:|---:|---:|
| Último funding positivo | +0,8719% | 11,1413% | -15,8401% | 72 |
| Funding acima de 0,5 bp | +0,5861% | 11,4551% | -16,5965% | 74 |
| Funding positivo com filtro de vol/basis | +0,3998% | 10,5241% | -15,3863% | 68 |

Essas regras encontraram funding, mas destruíram valor com turnover. O problema deixou de ser somente “há funding positivo?” e passou a ser “como evitar funding ruim sem pagar repetidamente para entrar e sair?”.

## 11. Margem e capital empregado

O modelo atual usa margem segregada e conservadora:

- US$ 100 de BTC spot ficam fora da conta do perp;
- o short recebe um buffer separado de 25%, 50% ou 100%;
- a fee de abertura reduz a margem;
- funding é creditado ou debitado na conta do perp;
- a manutenção simulada é 5% do nocional marcado mais uma fee estimada de fechamento;
- quando há violação no fechamento horário, as duas pernas são fechadas no próximo open e a estratégia permanece inativa.

Isto é uma política de estresse própria, não uma reconstrução histórica das liquidações da Bybit.

### 11.1 Piloto de 2026

| Buffer | Capital total | Líquido-base / nocional | Líquido-base / capital | Violações |
|---:|---:|---:|---:|---:|
| 25% | US$ 125 | +0,2486% | +0,1989% | 0 |
| 50% | US$ 150 | +0,2486% | +0,1657% | 0 |
| 100% | US$ 200 | +0,2486% | +0,1243% | 0 |

A ausência de violações não valida os buffers, pois o caminho do BTC quase não pressionou o short.

### 11.2 Rally de 2023–2024

| Buffer | Primeira violação | Exposição antes do fechamento | Resultado-base / nocional até fechar |
|---:|---|---:|---:|
| 25% | 23/10/2023 23:00 UTC | 6,82% | -0,4614% |
| 50% | 02/12/2023 20:00 UTC | 18,69% | +1,7593% |
| 100% | 26/02/2024 19:00 UTC | 44,27% | +7,8668% |

Todos os buffers falharam operacionalmente. Um resultado combinado positivo antes da violação não torna a política sustentável: o spot pode estar ganhando enquanto o colateral segregado do short é consumido.

Esse é o principal problema de estrutura de capital identificado até agora.

## 12. Zona morta e persistência

Foram testadas regras com thresholds de entrada/saída e permanência mínima de 24, 48 e 72 horas. Houve zero candidatos aprovados entre 54 combinações de regra, buffer e custo.

No cenário-base com buffer de 25%:

- always-on OOS: **+0,2410%**;
- melhor regra testada no período completo: **-3,6511%**;
- resultado OOS dessa regra: **-2,4508%**;
- turnover: 18 meios-giros.

A conclusão deve ser restrita: zonas de 24–72 horas falharam. Isso não rejeita políticas de semanas ou meses, que podem ter relação mais favorável entre persistência capturada e custo de giro.

## 13. Papel do HMM

O HMM é candidato a detectar estados latentes como:

- carry estável;
- euforia frágil;
- desalavancagem;
- transição ou neutralidade.

As features candidatas incluem funding, basis, open interest, volume, volatilidade, momentum, liquidações e liquidez, sempre disponíveis no instante da decisão.

O HMM não deve prever diretamente o preço do BTC. Seu output deve alimentar uma política de manter, reduzir ou não carregar a posição.

Ele só merece entrar no núcleo se:

1. o carry simples sobreviver em histórico longo e contínuo;
2. o desempenho depender de regimes identificáveis;
3. o HMM superar o melhor baseline simples fora da amostra em pelo menos duas dimensões relevantes, como retorno líquido, drawdown, estabilidade, Sharpe/Sortino ou eficiência de margem;
4. a melhora sobreviver a custos, seeds, número de estados e subperíodos.

Se isso não ocorrer, o HMM deve ser removido da proposta principal.

## 14. O que já foi estabelecido

### Evidências favoráveis

- O mercado paga funding relevante ao lado short em parte das observações.
- A posição fixed-quantity long spot + short perp neutralizou quase todo o movimento direcional no piloto.
- O always-on permaneceu positivo após taxas oficiais e no cenário-base.
- O problema possui mecanismo econômico e pergunta falsificável.
- O pipeline já diferencia execução, mark, funding, custos e margem.

### Evidências desfavoráveis

- O retorno líquido é pequeno para o capital empregado.
- O lucro desaparece no cenário de custo 3×.
- Regras reativas e zonas curtas são destruídas por turnover.
- Buffers segregados de até 100% falharam no rally histórico.
- Três meses não capturam ciclos suficientes de funding.
- Spread, slippage, capacidade e regras históricas de margem ainda não são observados diretamente.

### Veredito atual

```text
Mecanismo validado: parcialmente.
Viabilidade econômica validada: não.
Gestão de margem validada: não.
Valor incremental do HMM validado: não testado.
```

## 15. Próximos passos

### Prioridade 1 — estrutura de capital e margem

1. Adicionar buffers segregados de 150% e 200% ao rally e ao histórico contínuo.
2. Implementar uma política de margem cruzada, com haircut explícito para BTC spot como colateral.
3. Comparar segregated versus cross-margin em retorno sobre capital, pior utilização e violações.
4. Modelar transferências de colateral, latência e gatilhos de redução antes da liquidação.

**Critério de avanço:** existir pelo menos uma política operacional que atravesse episódios extremos sem violação e com retorno sobre capital plausível.

### Prioridade 2 — histórico contínuo e dados

1. Construir uma série contínua de pelo menos 2021–2026.
2. Validar, por timestamp, spot, perp last, mark, index, funding, volume e open interest.
3. Separar desenvolvimento, validação e teste final intocado.
4. Preservar manifests, hashes, cobertura e regras de preenchimento.

**Critério de avanço:** resultados não dependerem do piloto de três meses nem de um único rally selecionado.

### Prioridade 3 — custos executáveis

1. Obter bid/ask histórico ou snapshots de order book quando possível.
2. Estimar slippage por tamanho e capacidade.
3. Documentar fees históricas, tiers e rebates, sem aplicar retroativamente apenas a tabela atual.
4. Acrescentar custos de stablecoin, transferência, custódia e financiamento quando aplicáveis.

**Critério de avanço:** carry líquido positivo sob uma faixa de custos observável e conservadora, não apenas sob uma proxy arbitrária.

### Prioridade 4 — baselines lentos

1. Testar decisões semanais e horizontes mínimos de 7, 30, 60 e 90 dias.
2. Usar benefício esperado acumulado maior que o custo completo de um ciclo.
3. Testar histerese e rebalanceamento parcial, não apenas posição binária.
4. Comparar sempre com always-on e caixa.

**Critério de avanço:** reduzir risco ou uso de margem sem destruir retorno líquido por turnover.

### Prioridade 5 — protocolo estatístico

1. Agregar cashflows em retornos diários antes de Sharpe, Sortino e volatilidade anualizada.
2. Executar walk-forward sem vazamento temporal.
3. Reportar drawdown, turnover, exposição, funding negativo, basis, margem e estabilidade por subperíodo.
4. Fazer stress tests de custos, gaps, indisponibilidade e mudanças de funding.

### Prioridade 6 — HMM apenas após os gates anteriores

1. Começar com dois ou três estados interpretáveis.
2. Treinar somente com dados passados em cada janela.
3. Converter probabilidades em política com limites de turnover e margem.
4. Fazer ablações contra baselines lentos.
5. Retirar o HMM se não houver ganho incremental fora da amostra.

## 16. Condições de abandono ou reformulação

A tese deve ser abandonada ou reformulada se o histórico contínuo mostrar que:

- o funding bruto não cobre custos executáveis de forma recorrente;
- o capital necessário para evitar liquidação derruba o retorno para um nível irrelevante;
- a rentabilidade depende de um único período ou venue;
- qualquer filtro útil exige turnover maior que o carry capturado;
- a camada de regime não supera baselines simples fora da amostra;
- a capacidade real é insuficiente para o objetivo do projeto.

Uma conclusão negativa, se obtida com rigor, ainda atende ao espírito analítico do desafio. O objetivo não é preservar a ideia a qualquer custo, mas descobrir se existe um prêmio explorável e operacionalizável.

## 17. Artefatos reproduzíveis

- Metodologia: `docs/methodology.md`
- Resultado do piloto: `reports/pilot_findings.md`
- Margem no piloto: `reports/margin_findings.md`
- Zona morta: `reports/dead_zone_findings.md`
- Rally histórico: `reports/rally_margin_findings.md`
- Resumos numéricos: `reports/*_summary.csv`
- Motor de P&L: `src/run_baselines.py`
- Política de margem: `src/margin.py`
- Testes: `tests/test_run_baselines.py` e `tests/test_margin.py`

No estado atual, a formulação mais honesta e competitiva para o projeto é:

> Não tentamos prever o próximo preço do Bitcoin. Testamos quando vale fornecer a ponta short demandada por traders alavancados, protegendo a direção com spot e recusando o trade quando custos, basis ou margem tornam o carry economicamente frágil.
