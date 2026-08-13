# Knowledge base — Lagrangian Bulls

Esta pasta consolida o contexto herdado do projeto ChatGPT **Lagrangian Bull**. Os documentos foram copiados como referências locais para que o desenvolvimento possa acontecer inteiramente neste repositório.

## Ponto de partida

O documento que governa a pesquisa é [`Core/Relatorio_Funding_Perpetuos_e_Tese_HMM.md`](Core/Relatorio_Funding_Perpetuos_e_Tese_HMM.md).

A tese atual é capturar funding positivo de perpétuos de BTC mantendo exposição aproximadamente neutra ao preço: **long spot + short perp** no mesmo nocional. O HMM é uma hipótese de ferramenta para selecionar regimes em que o carry líquido esperado compensa custos, risco de basis e risco de margem; ele não é a tese por si só.

## Organização e prioridade

1. `Core/` — tese, perguntas de pesquisa, hipóteses e protocolo de backtest. Fonte prioritária para implementação.
2. `Guidelines/` — padrão de raciocínio, crítica metodológica e gestão da pesquisa.
3. `References/Official/` — edital, guia e aulas do Desafio Quant AI; regras oficiais sempre prevalecem sobre o restante.
4. `References/Examples/` — projetos de edições anteriores, úteis para narrativa e formato, não como evidência da estratégia.
5. `Processed/` — sínteses de trabalho derivadas das fontes; servem para navegação, mas os documentos em `Core/` e as fontes oficiais continuam sendo a referência.

## Convenções

- Preserve os PDFs como fontes brutas: não editar nem depender deles como dados de execução.
- Coloque novos dados, notebooks, código e resultados fora de `Knowledge/` (por exemplo, em `data/`, `src/`, `notebooks/` e `reports/`).
- Registre decisões e evidências novas em documentos versionados, distinguindo claramente hipótese, resultado reproduzível e fato oficial.
- Antes de implementar HMM/RL ou outro modelo complexo, o relatório recomenda construir a base point-in-time e baselines simples com custos e fricções.

## Proveniência

Conteúdo copiado e processado em 12 de agosto de 2026 de `/Users/bruno/.codex/.chatgpt-projects/g-p-6a2334eb16d88191a4fd0f51aef3e3b5`.
