# Brief de implementação — Funding Carry com HMM

## Objetivo

Testar se há retorno líquido, repetível e adequadamente remunerado ao fornecer a ponta short de BTC perp quando o funding é positivo, mantendo o risco direcional aproximadamente neutro por meio de BTC spot.

```text
funding positivo -> comprar BTC spot + vender BTC perp no mesmo nocional
```

O retorno buscado não é previsão direcional de BTC. É o funding recebido, mais ou menos a variação do basis, líquido de execução, margem e demais fricções.

## Pergunta de pesquisa

Em quais condições o funding futuro, mais a dinâmica esperada do basis, supera taxas, spreads, slippage, risco de margem e o risco de inversão do funding?

## Sequência de construção

1. **Data spike:** uma única venue líquida; BTC spot e BTC perp compatíveis; coletar um recorte pequeno e auditável.
2. **Motor de P&L:** simular o par hedgeado com timestamps corretos, funding efetivamente conhecido, custos, basis e margem.
3. **Baselines:** carry sempre que funding > 0; limiar que cobre custos; filtro de volatilidade; filtro de basis/OI.
4. **Validação:** walk-forward, execução em `t+1`, subperíodos de bull/bear/choque e sensibilidade a custos.
5. **HMM:** somente se os baselines tiverem carry líquido, mas com desempenho dependente de regime. Comparar o HMM com o melhor baseline fora da amostra.

## Dados mínimos point-in-time

| Série | Uso |
|---|---|
| spot, perp, mark price e index price | P&L hedgeado e basis |
| funding realizado/anunciado e horários | receita de carry sem olhar o futuro |
| volume, open interest e spreads | filtros, capacidade e regimes |
| volatilidade e retornos | risco e regimes |
| regras da venue, taxas e margem | simulação executável |

Liquidações e fluxos são opcionais: entram apenas se houver histórico confiável e carimbado no tempo.

## Política candidata de regimes

| Regime | Assinatura | Ação |
|---|---|---|
| Carry estável | funding positivo persistente, vol/basis controlados | entrar ou manter |
| Euforia frágil | funding e basis altos, OI/vol acelerando | reduzir e aumentar margem de segurança |
| Desalavancagem | funding cai/inverte, vol alta, liquidações | fechar; não carregar |
| Transição | sinais mistos | não operar ou exposição baixa |

O HMM deve emitir probabilidades de estado. A política, não o HMM isoladamente, transforma isso em peso entre caixa, spot e short perp sob limites de margem, turnover e drawdown.

## Critério de aceitação

A versão com regimes só avança se superar o melhor baseline simples fora da amostra em pelo menos duas dimensões relevantes — retorno líquido, drawdown, Sharpe/Sortino, estabilidade por subperíodo ou eficiência de margem — sem depender de um episódio isolado. Caso contrário, o HMM deixa de ser parte central da estratégia.

## Riscos que o backtest precisa tornar visíveis

- funding invertido durante a posição;
- abertura do basis contra a posição;
- liquidação ou falta de colateral apesar do hedge econômico;
- taxas, spread, slippage e capacidade;
- risco de venue, custódia e stablecoin;
- viés de look-ahead, principalmente no funding e no sinal.

Fonte: `../Core/Relatorio_Funding_Perpetuos_e_Tese_HMM.md`.
