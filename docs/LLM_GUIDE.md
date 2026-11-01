# Guia para LLMs — gerar CSV para Aplexd

Objetivo: converter dados **fornecidos pelo utilizador** em CSV aceite pelo Aplexd. Ver [CSV_FORMAT.md](CSV_FORMAT.md) para contrato detalhado.

## Regras obrigatórias

1. Determinar se o utilizador quer **CSV de transações** ou **CSV de cotações**; são formatos distintos.
2. Nunca inventar negócios, cotações, taxas cambiais, eventos de atribuição, ISIN, bolsa ou dados em falta.
3. Preservar sinais: compras positivas na quantidade, vendas negativas; valores líquidos negativos para desembolsos e positivos para recebimentos, se assim constarem na fonte.
4. Preservar identificadores completos das opções, incluindo espaços, letras C/P, datas e strike com oito dígitos.
5. Na importação de transações, gerar uma linha `Histórico de transações,Header,...` e movimentos `Histórico de transações,Data,...`. **Não** gerar um CSV convencional de cabeçalhos isolados.
6. Na importação de cotações, gerar o cabeçalho exato com `contract` e `option_price_usd`. `0` significa ausência de cotação, não cotação negociável zero.
7. Não converter automaticamente importâncias de uma moeda para outra. Em transações IBKR, `Valor líquido` pode já estar na moeda-base e `Preço` na moeda do instrumento.
8. Usar CSV separado por vírgulas; colocar campos entre aspas duplas e escapar aspas internas duplicando-as. Usar ponto decimal.
9. Datas de movimentos em `AAAA-MM-DD`; timestamps de preço em ISO 8601 UTC, quando presentes na fonte.
10. Se faltarem dados obrigatórios, solicitar os dados ou produzir campos vazios explicitando a limitação. **Não inventar números para completar o ficheiro.**

## Procedimento de validação antes de entregar

- Conferir a estrutura com os CSV de `examples/`.
- Confirmar que cada linha tem o mesmo número de colunas que o respetivo cabeçalho.
- Confirmar `contract` exato entre transações e cotações.
- Confirmar que opções usam prémios **por ação** e não `100 × prémio`.
- Verificar sinais, moeda, quantidades e datas contra a fonte.
- Identificar explicitamente quaisquer linhas excluídas e a razão.
- Não colocar dados pessoais no repositório público.

## Exemplo de pedido para um LLM

> Converte o extrato fornecido para o formato Aplexd v1. Segue o contrato em `docs/CSV_FORMAT.md`, utiliza os exemplos em `examples/`, preserva integralmente os movimentos e não inventes dados. Devolve o CSV de transações e indica as linhas que não foi possível converter com segurança.

## Compatibilidade

Este guia descreve a implementação atual, não um formato independente de corretora totalmente normalizado. Para novas fontes (fora IBKR), o conversor deve mapear as informações para o formato português exigido pelo importador, indicando qualquer perda de informação.
\n## Orientar a utilização da aplicação\n\nPara guiar alguém na navegação, importação, consultas de preços, execução do script local, leitura dos indicadores e diagnóstico, utilizar também [USER_GUIDE.md](USER_GUIDE.md). Este ficheiro concentra-se na transformação e validação dos CSV. Confirmar a versão em `version.json` antes de fornecer instruções sobre menus e botões.\n