# Lições das referências

## Materiais oficiais

- A masterclass Quant e o guia convergem em uma mensagem: dados -> processamento -> decisão objetiva -> simulação histórica. Sofisticação não substitui cadeia causal, regras de execução e avaliação crítica.
- Treino, validação e teste precisam respeitar o tempo; o guia sugere, conforme a complexidade, divisão temporal e walk-forward. No carry, isto é especialmente crítico porque funding e preços têm horários de publicação/crédito distintos.
- A aula de GenAI reforça uma oportunidade de apresentação: documentar o processo de pesquisa e engenharia ajuda a pontuar sem alegar que o LLM produziu alpha.

## Trabalhos anteriores

### 14-BIS

Estratégia de ações líquidas do Ibov combinando tweets, dados contábeis/macro e redes neurais para sinal diário. A lição positiva é a narrativa bem estruturada — universo, holding period, benchmark e fontes. A cautela é que grande volume de features, NLP e modelo complexo elevam muito a exigência de validação.

### Ocellus

Estratégia de mini-dólar baseada em sentimento de headlines e filtros de momentum. O projeto declara execução no dia seguinte ao sinal para evitar look-ahead e separa treino/teste, bons hábitos a manter. Também expõe a armadilha que devemos evitar: otimização de muitos limites gerou uma solução pouco ativa e Sharpe menor; complexidade não demonstrou ganho claro.

## Aplicação direta ao Lagrangian Bulls

O diferencial não deve ser “HMM em cripto”. Deve ser uma tese de carry hedgeado, uma simulação economicamente realista e uma camada de regime que prove melhorar uma regra simples. O relatório de funding já contém esse enquadramento; a implementação precisa preservá-lo.

Fontes: `../References/Official/Aula 1 Quant.pdf`, `../References/Official/Aula 1 - GenAI Para o Mercado Financeiro.pdf`, `../References/Examples/14BIS.pdf` e `../References/Examples/ocellus.pdf`.
