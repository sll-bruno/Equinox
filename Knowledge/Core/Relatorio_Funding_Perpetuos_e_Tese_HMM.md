# Lagrangian Bulls — Relatório de Discussão

## Funding em perpétuos, carry neutro em preço e tese com HMM

**Status:** documento de trabalho. Consolida a conversa até aqui. Não representa resultado de backtest, recomendação de investimento nem decisão final de escopo.

## 1. Resumo executivo

A hipótese em investigação é usar o mercado de futuros perpétuos de cripto para capturar o *funding* recebido por quem fornece a ponta menos demandada do contrato, reduzindo a exposição ao preço do Bitcoin por meio de um hedge no mercado spot.

A operação-base, quando o funding é positivo, é:

```text
comprar BTC spot + vender BTC perp no mesmo tamanho
```

O BTC spot e o perp vendido tendem a se compensar quando o preço do BTC sobe ou cai. O retorno pretendido é o funding recebido pelos vendidos, menos todos os custos e riscos. A inovação candidata não é “prever BTC com HMM”; é usar um modelo de regimes para decidir **quando o carry provavelmente será líquido, persistente e adequadamente remunerador** e quanto risco é sensato assumir.

Pergunta de pesquisa central:

> Em quais regimes de mercado o funding futuro, somado à dinâmica do basis, supera taxas, spreads, risco de margem e demais fricções de uma operação spot + perp hedgeada?

## 2. Por que esta tese pode ser competitiva no Desafio Quant AI

O edital dá 20% para conceito/criatividade, 20% para modelagem, 15% para backtest e mitigação de vieses, 15% para análise e 15% para uso de GenAI. Também afirma que complexidade não é o objetivo: a estratégia precisa ser clara, sistemática, replicável e defensável. O foco desta tese é atender a esse enquadramento: um mecanismo econômico concreto, uma decisão operacional objetiva e um teste que pode invalidar a ideia.

Em vez de prometer “prever o próximo preço do Bitcoin”, a narrativa é:

> Participantes que desejam exposição comprada e alavancada em perpétuos podem pagar funding para manter essa posição. A estratégia fornece a ponta short, protege o risco direcional com BTC spot e só carrega esse risco quando a remuneração esperada justifica as fricções e os riscos de regime.

Isso posiciona o projeto como **controle de risco e alocação**, não como previsão direcional. O HMM é uma ferramenta possível para esse controle; não é a tese em si.

## 3. Perpétuos: explicação do contrato

Um perpétuo (*perpetual future* ou *perp*) é um contrato que acompanha o preço do BTC, mas não entrega Bitcoin e não possui data de vencimento.

### 3.1 Long e short

- **Long:** ganha se o BTC sobe e perde se o BTC cai.
- **Short:** ganha se o BTC cai e perde se o BTC sobe.

Exemplo: BTC vale US$ 100 mil. Bruno abre um long de 1 BTC perp e Schade abre um short de 1 BTC perp. Se o BTC sobe para US$ 105 mil, Bruno ganha US$ 5 mil e Schade perde US$ 5 mil. A exchange transfere esse valor entre as margens das duas pontas; nenhum Bitcoin precisa ser entregue.

O preço de entrada não é um acordo para comprar BTC no futuro. Ele apenas define a referência para calcular o lucro ou a perda da posição.

### 3.2 Margem, alavancagem e liquidação

Para abrir o perp, a pessoa deixa uma garantia, chamada **margem**. É possível controlar uma posição maior que a margem depositada — alavancagem — mas isso aumenta o risco de liquidação.

Exemplo: alguém deposita US$ 10 mil e abre long de US$ 100 mil em BTC perp (10x). Uma queda próxima de 10% pode consumir a margem; antes de o saldo ficar negativo, a exchange fecha a posição automaticamente. A liquidação é o que impede que a exchange fique exposta a um prejuízo não coberto.

Mesmo sem alavancagem, a margem varia conforme o P&L. Uma posição de US$ 100 mil garantida por US$ 100 mil perde US$ 10 mil de margem se o BTC cair 10%. A posição pode permanecer aberta enquanto satisfizer a margem de manutenção e o operador suportar os custos recorrentes.

### 3.3 Quem está nas pontas

Economicamente, todo long tem um short correspondente. Na prática, a exchange pode fazer o casamento no livro de ordens e gerir a posição agregada, sem “amarrar” permanentemente uma pessoa específica à outra.

Participantes típicos:

- Longs: traders buscando alta, fundos tomando risco direcional, participantes que preferem derivativo a custódia spot, market makers com inventário temporário.
- Shorts: apostadores em queda, holders/mineradores protegendo BTC que já possuem, market makers e arbitradores.
- Exchange ou protocolo: infraestrutura que casa ordens, exige margem, calcula P&L, funding e liquidações. Não precisa ser a contraparte econômica final da posição.

## 4. O que é funding

Funding é uma **taxa periódica entre longs e shorts**. Não é, em essência, uma comissão que a exchange recebe. A função é manter o preço do perp próximo ao preço do BTC no mercado spot.

Como o perp não vence, não há uma data final que force seu preço a convergir para o spot. O funding cria um incentivo econômico para reduzir desvios persistentes.

### 4.1 Funding positivo

Funding de `+0,01%` a cada 8 horas significa:

```text
longs pagam shorts
```

Normalmente isso ocorre quando o perp está acima do índice spot e há demanda relativamente maior pela ponta comprada. O custo torna permanecer long menos atraente e torna ficar short mais atraente, ajudando a puxar o perp de volta para perto do spot.

### 4.2 Funding negativo

Funding de `-0,01%` a cada 8 horas significa:

```text
shorts pagam longs
```

Normalmente isso ocorre quando há pressão relativamente maior para ficar vendido e o perp está abaixo do índice spot.

### 4.3 Funding não prevê direção do BTC

Funding positivo **não** significa que BTC necessariamente subirá. Ele apenas indica quem paga naquela janela. O BTC pode cair enquanto o funding segue positivo se os participantes mantiverem demanda para ficar long. Em quedas severas, o funding pode cair ou inverter à medida que longs são liquidados ou reduzem suas posições — mas isso é um padrão empírico a testar, não uma regra garantida.

### 4.4 Como o spot de referência é calculado

Em geral, a venue constrói um **índice spot** a partir de preços de várias exchanges líquidas, normalmente com pesos e regras contra valores anômalos. O funding de cada venue usa a própria fórmula, que costuma combinar:

- diferença entre o preço do perp e o índice spot (*premium*);
- componente de juros/base, quando aplicável;
- limites para evitar taxas extremas.

Consequência metodológica: funding, preço perp e índice spot precisam ser documentados com precisão **na mesma venue e no mesmo timestamp**. Não é seguro misturar séries sem conhecer a metodologia de cálculo.

## 5. Como ganhar dinheiro com funding

O princípio é estar do lado que recebe a taxa e neutralizar a exposição direcional ao BTC.

### 5.1 Caso A: funding positivo

Quando o funding é positivo, shorts recebem. A operação neutra é:

```text
comprar 1 BTC spot + vender 1 BTC perp
```

Exemplo simplificado:

- BTC spot = US$ 100 mil.
- Venda de 1 BTC perp = US$ 100 mil nocional.
- Funding = +0,01% a cada 8 horas.

No horário do funding, o short recebe aproximadamente US$ 10 (`0,01% × 100.000`).

Se o BTC cair para US$ 90 mil:

- spot: -US$ 10 mil;
- short perp: +US$ 10 mil;
- efeito direcional aproximado: zero;
- funding: +US$ 10, antes de custos.

Se o BTC subir para US$ 110 mil, acontece o inverso: o BTC spot ganha US$ 10 mil e o short perde US$ 10 mil. O funding continua sendo a fonte buscada de retorno enquanto positivo.

### 5.2 Caso B: funding negativo

Quando funding é negativo, longs recebem. Para ficar neutro em preço, a construção é mais trabalhosa:

```text
tomar 1 BTC emprestado e vender spot + comprar 1 BTC perp
```

Se BTC sobe, a ponta spot vendida perde e o long perp ganha; se BTC cai, a ponta spot vendida ganha e o long perp perde. A estratégia recebe funding no long, mas tem um custo adicional importante: o empréstimo de BTC (*borrow*). Só faz sentido se funding esperado superar borrow, taxas, spreads e riscos.

Por simplicidade e viabilidade, a primeira versão pode focar exclusivamente no funding positivo. O caso negativo pode entrar como extensão ou benchmark de completude.

## 6. Basis: por que importa

**Basis** é a diferença entre o preço do perp e o preço spot:

```text
basis = preço do perp - preço spot
```

Basis positivo significa perp acima do spot. Não é automaticamente ruim; pode ser parte do retorno da operação. Se o perp está a US$ 105 mil e o spot a US$ 100 mil, vender o perp e comprar spot trava uma diferença inicial favorável de US$ 5 mil, caso ela converja.

Mas, como o perp não vence, não há obrigação de o basis zerar em uma data definida. Ele pode aumentar de US$ 5 mil para US$ 8 mil. Para quem está short perp e long spot, essa abertura gera uma perda temporária aproximada de US$ 3 mil, mesmo que o BTC spot não se mova.

Logo, a regra correta não é “evitar basis alto”, e sim avaliar:

```text
funding esperado + convergência esperada do basis
versus
risco de abertura do basis + custos + margem exigida
```

## 7. Taxas, custos e riscos da operação

Para a posição `long spot + short perp`, o resultado não é apenas funding.

```text
P&L líquido = funding recebido
            + variação favorável de basis
            - funding pago
            - taxas de negociação
            - spread e slippage
            - custos de margem/colateral
            - perdas de basis
            - custos de transferência e conversão, se existirem
```

### 7.1 Custos explícitos

1. Taxa para comprar spot.
2. Taxa para vender/abrir o perp short.
3. Taxa para vender o spot na saída.
4. Taxa para recomprar/fechar o perp short.
5. Spread de compra e venda em ambas as pernas.
6. Slippage, sobretudo se a ordem for grande frente à liquidez disponível.
7. Funding pago, caso a taxa inverta durante a posição.
8. Custos de rede, transferência e conversão de BRL/stablecoin, se a operação usar venues distintas.
9. Custo de empréstimo de BTC, apenas no caso de funding negativo com spot short.

### 7.2 Riscos econômicos e operacionais

- **Inversão do funding:** o short deixa de receber e passa a pagar.
- **Basis risk:** spot e perp não compensam perfeitamente se a diferença entre eles se mover.
- **Margem e liquidação:** uma alta forte no BTC pressiona o short perp; o lucro da ponta spot pode não estar disponível como colateral no momento certo.
- **Risco de venue:** custódia, indisponibilidade, insolvência ou alteração de regras numa CEX; falha de smart contract, oracle, bridge ou liquidez numa DEX.
- **Risco de stablecoin:** colateral e caixa podem ter risco de emissor/descolamento.
- **Risco de capacidade:** um retorno histórico em volume pequeno não prova que se pode alocar capital grande sem afetar preço e custos.
- **Risco regulatório/tributário:** execução e retorno econômico podem variar com a jurisdição e com regras aplicáveis.

## 8. CEX, DEX e DeFi

A tese econômica não depende de a execução ser centralizada ou descentralizada.

| Aspecto | CEX | DEX / DeFi |
|---|---|---|
| Custódia | A exchange mantém o colateral | Carteira e/ou smart contract do protocolo |
| Risco dominante | Empresa, custódia, bloqueio, insolvência | Smart contract, oracle, bridge, liquidez |
| Dados e execução | Em geral mais diretos e líquidos | Dados on-chain, arquitetura mais variável |
| Custos | Fees e spread | Fees, spread e possivelmente gas |
| Lógica de funding | A mesma | A mesma |

O interesse de DeFi é infraestrutura financeira programável e, muitas vezes, dados e regras observáveis on-chain. O prêmio econômico, porém, não nasce por algo ser DeFi: ele nasce do desequilíbrio entre demanda long e short.

Recomendação para a primeira pesquisa: escolher uma única venue líquida, documentar suas regras e não misturar CEX e DEX cedo demais. CEX versus DEX pode ser um teste de robustez posterior.

## 9. Relevância do mercado de perpétuos

Perpétuos não são um submercado irrelevante. A melhor métrica aqui é volume negociado e open interest, não market cap dos tokens — comparar market cap com volume de contratos mistura estoque e fluxo.

- Documento ligado à CFTC cita dados da Kaiko segundo os quais perpétuos responderam por 68% de todo o volume de negociação de Bitcoin em 2025 e derivativos por mais de 75% de toda a atividade em cripto. [CFTC](https://www.cftc.gov/filings/ptc/ptc0602265036.pdf)
- A CoinGecko estima que CEXs de perpétuos processaram mais de US$ 85,3 trilhões em 2025; DEXs de perpétuos, US$ 6,2 trilhões. [CoinGecko](https://assets.coingecko.com/reports/2026/CoinGecko-2026-State-of-Crypto-Perpetuals-Report.pdf?ctcid=6c4e2f39-0fbe-4b04-8e5f-9683a648188e)
- Uma estimativa agregada da Cboe aponta aproximadamente US$ 111,5 trilhões em volume anual de derivativos cripto em 2025, contra US$ 25,3 trilhões em spot — cerca de 4,4 vezes o turnover spot. [Cboe](https://www.cboe.com/insights/posts/beyond-etfs-how-derivatives-tokenization-are-reshaping-crypto)

Isto reforça a narrativa de que perps são infraestrutura central para negociação, transferência de risco e descoberta de preço em cripto. Não prova, por si só, que a estratégia de carry é rentável após custos.

## 10. A tese candidata, formulada com precisão

> Em certos regimes, a demanda persistente por exposição comprada em perpétuos gera funding positivo suficiente para remunerar o lado short. Ao comprar spot e vender perp no mesmo tamanho, reduzimos o risco direcional do BTC. Um modelo de regimes e uma política de alocação podem selecionar os episódios em que o carry líquido esperado supera custos, risco de basis, margem e risco de desalavancagem.

Em linguagem curta para apresentação:

> Não tentamos prever o próximo preço do Bitcoin. Fornecemos a ponta short que o mercado demanda, protegemos preço com spot e usamos sinais de regime para decidir quando esse aluguel da alavancagem compensa o risco.

### 10.1 O que a tese não afirma

- Funding positivo não é dinheiro grátis.
- Funding positivo não prevê alta de BTC.
- HMM não é um oráculo de crises nem garante persistência do funding.
- Volume grande de perp não garante capacidade de execução em qualquer tamanho.
- Não existe evidência de performance até existir backtest reprodutível e líquido de custos.

## 11. Onde entra o HMM

O HMM (*Hidden Markov Model*) é candidato a inferir estados latentes do mercado a partir de variáveis observáveis. Ele não deve ter como alvo “BTC sobe ou cai”, mas a condição econômica de carregar ou não o trade de funding.

Entradas candidatas, sempre disponíveis no momento da decisão:

- funding atual, histórico e velocidade de mudança;
- basis perp menos spot;
- open interest e variação de open interest;
- volume;
- volatilidade realizada;
- retorno e momentum;
- liquidações, somente se a fonte e os timestamps forem confiáveis;
- spreads e medidas de liquidez;
- eventualmente dados de fluxo/posição, quando houver cobertura histórica adequada.

Estados conceituais possíveis:

| Regime | Possível assinatura | Regra de decisão |
|---|---|---|
| Carry estável | Funding positivo moderado e persistente; vol e basis controlados | Entrar ou manter |
| Euforia frágil | Funding/basis altos; OI acelerando; vol crescente | Reduzir e exigir maior margem de segurança |
| Desalavancagem | Funding caindo/negativo; vol alta; liquidações | Fechar; não carregar |
| Neutro/transição | Sinais mistos | Não operar ou operar pouco |

O HMM gera probabilidades dos estados. A política final pode usar essas probabilidades para dimensionar a exposição entre caixa, BTC spot e short perp, com limites explícitos de margem, turnover, concentração e drawdown.

## 12. Como resolver empiricamente a pergunta

### 12.1 Definir o alvo certo

Para cada instante \(t\), simular a operação que seria aberta com dados disponíveis naquele instante e mantida por um horizonte fixo — por exemplo, 24 horas, 72 horas ou 7 dias. O alvo é:

```text
P&L líquido realizado no horizonte
```

e não simplesmente “funding foi positivo?”.

### 12.2 Construir a base point-in-time

1. Escolher um ativo e uma venue líquida, inicialmente BTC spot e BTC perp no mesmo local.
2. Coletar funding, mark price, index price, preço spot, preço perp, volume, OI e demais sinais no timestamp correto.
3. Registrar a fórmula e a periodicidade de funding da venue.
4. Aplicar taxas, spreads e slippage conservadores.
5. Modelar margem e evitar pressupor que ganhos do spot cobrem instantaneamente perdas do perp.

### 12.3 Começar com baselines simples

Antes de qualquer HMM:

1. Carry sempre ligado, quando funding é positivo.
2. Carry apenas acima de um limiar de funding que cubra os custos.
3. Carry com filtro simples de volatilidade.
4. Carry com filtro simples de basis e/ou OI.

Depois:

5. Carry condicionado ao HMM e à política de dimensionamento.

### 12.4 Hipótese testável

> A estratégia de carry condicionada ao regime deve superar o melhor baseline simples em pelo menos duas dimensões relevantes fora da amostra — por exemplo retorno líquido, drawdown, Sharpe/Sortino, estabilidade entre subperíodos ou eficiência de margem — sem depender de um único episódio de mercado.

Se não superar, a conclusão correta é que HMM não agregou valor incremental e deve sair do núcleo.

## 13. Protocolo de backtest e rigor

- Separar desenvolvimento, validação e teste final intocado.
- Preferir walk-forward; retreinar/recalibrar somente com dados passados.
- Entrar e executar em \(t+1\), não no mesmo preço usado para formar o sinal.
- Usar funding efetivamente conhecido/creditado no horário aplicável; não olhar taxa futura.
- Documentar todas as configurações testadas e aplicar correção por múltiplos testes quando pertinente, como Deflated Sharpe Ratio.
- Testar custos em cenários conservadores e fazer sensibilidade de spread/slippage.
- Rodar subperíodos: bull, bear, choque, baixa e alta volatilidade.
- Medir drawdown, tempo em margem, turnover, exposição, pior abertura de basis e episódios de funding negativo.
- Verificar estabilidade entre seeds, número de estados e janelas do HMM.
- Fazer ablações: retirar HMM, retirar OI, retirar basis, retirar filtro de volatilidade etc.

## 14. Uso de GenAI

GenAI é obrigatória no desafio, mas seu uso precisa ser prático e documentável. Aplicações válidas para esta tese:

- organização e red-team da hipótese;
- apoio na implementação e revisão de código, com validação humana;
- checagem de riscos de look-ahead, timestamps e custos;
- leitura estruturada de documentação de venues e fórmulas de funding;
- síntese de resultados, gráficos e preparação da defesa técnica;
- eventual interpretação de textos on-chain/notícias, somente se houver hipótese adicional e dados point-in-time confiáveis.

GenAI não deve ser apresentada como evidência de rentabilidade. Dados, código, escolhas e resultados precisam permanecer auditáveis e compreendidos pelo time.

## 15. Decisões abertas

1. **Universo inicial:** somente BTC ou BTC + ETH? Recomendação: BTC primeiro.
2. **Venue:** qual exchange/protocolo tem dados históricos confiáveis de funding, spot, perp, OI e regras documentadas?
3. **Frequência/horizonte:** janelas de funding, 24h, 72h ou 7 dias?
4. **Escopo inicial:** apenas funding positivo ou também estratégia simétrica para funding negativo?
5. **Política de margem:** qual colateral e qual limite de utilização evitam liquidações artificiais?
6. **Dados complementares:** liquidações/OI realmente têm disponibilidade point-in-time e qualidade suficientes?
7. **HMM:** dois ou três estados; quais features entram; com que frequência reestimar?
8. **Critério de abandono:** qual ganho mínimo líquido e estável justifica a complexidade adicional sobre filtros simples?

## 16. Próximo passo recomendado

Fazer um *data spike* curto antes de travar o HMM:

1. selecionar uma venue e baixar um recorte pequeno de BTC spot, BTC perp e funding;
2. reproduzir o P&L de `long spot + short perp` com custos conservadores;
3. construir os quatro baselines simples;
4. identificar empiricamente se existem períodos com carry líquido recorrente;
5. só então especificar o modelo de regime.

Se o carry simples não sobreviver a custos e a dinâmica de basis/margem, HMM não o salvará. Se sobreviver mas sofrer em regimes identificáveis, teremos uma tese muito mais forte para a camada de regime e para o motor Lagrangiano de alocação.

