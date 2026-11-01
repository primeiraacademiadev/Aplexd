# Aplexd — Contratos CSV (v1)

Esta especificação descreve **o importador atualmente implementado em `index.html`**. Existem dois formatos independentes: transações e cotações. O formato não é um CSV genérico universal.

## 1. Histórico de transações (IBKR em português)

- CSV UTF-8, separado por **vírgulas**, aspas duplas para escapar campos. Ponto como separador decimal recomendado.
- O programa procura uma linha cujo primeiro campo é exatamente `Histórico de transações` e cujo segundo campo é exatamente `Header`. Esta linha determina os índices das colunas.
- Os movimentos têm primeiro campo `Histórico de transações` e segundo `Data`; as outras secções são ignoradas pelo parser atual.
- Cabeçalhos lidos: `Data`, `Símbolo`, `Descrição`, `Tipo de transação`, `Quantidade`, `Preço`, `Moeda do preço`, `Valor bruto`, `Taxa de corretagem` e `Valor líquido`. Os nomes devem coincidir exatamente. Outras colunas podem existir.
- `Conta` é incluída nos exemplos apenas para imitar a estrutura IBKR; atualmente não é usada pelo programa.
- Datas: `AAAA-MM-DD`, para ordenação cronológica.
- Tipos processados para posições: `Compra`, `Venda`, `Atribuição`. Algumas operações societárias são tratadas em regras específicas; dividendos e retenções são lidos em tipos específicos.
- Quantidade positiva numa compra, negativa numa venda. Para uma short, a abertura é habitualmente uma venda negativa; o fecho é uma compra positiva.
- `Valor líquido` já está na moeda-base do extrato (normalmente EUR), **com sinal**: desembolso negativo; recebimento positivo. Não converter novamente esse campo. `Preço` e `Moeda do preço` referem-se à cotação do instrumento.
- Para opções, `Símbolo` usa o padrão semelhante ao OCC: `ABCD 261120P00025000` = put, 20/11/2026, strike 25.000. O parser extrai strike, maturidade e tipo do símbolo.
- Incluir **todas** as execuções, despesas e eventos disponíveis; não inventar movimentos de fecho ou atribuições ausentes.
- Uma linha `Atribuição` pode representar ações resultantes, e não o próprio contrato original. Os resultados agregados continuam sujeitos a reconciliação.

### Exemplo fictício de transações

Ver [examples/transacoes_demo.csv](../examples/transacoes_demo.csv). Os símbolos, valores e movimentos são inventados. Não são recomendações de investimento.

## 2. CSV de cotações

Este formato pode ser exportado no botão **Exportar cotações CSV** e importado no botão **Importar cotações**.

**Obrigatórios no cabeçalho:** `contract`, `option_price_usd`.

**Colunas disponíveis na exportação** (ordem apresentada por conveniência, mas o importador encontra as colunas pelo nome):

| Coluna | Significado |
|---|---|
| `contract` | Chave exata do contrato no CSV de transações; para ações é o símbolo |
| `underlying` | Símbolo do subjacente |
| `type` | `STOCK` ou `OPTION` |
| `quantity` | Quantidade da posição; usada para referência no CSV, não altera as posições |
| `option_price_usd` | Preço por ação da opção ou ação; **não** preço por contrato; `0` equivale a não preenchido |
| `underlying_price_usd` | Preço da ação/subjacente, partilhado pelo grupo; `0` = não preenchido |
| `iv_percent` | Volatilidade implícita anual, em **pontos percentuais** (ex.: `35`) |
| `rate_percent` | Juro anual em pontos percentuais |
| `dividend_percent` | Dividend yield em pontos percentuais |
| `expiry` | Data de vencimento informativa (AAAA-MM-DD) |
| `option_type` | `C` ou `P`, informativo |
| `strike` | Preço de exercício, informativo |
| `quote_timestamp_utc` | Timestamp ISO 8601 do preço do contrato, se conhecido |
| `underlying_timestamp_utc` | Timestamp ISO 8601 do subjacente, se conhecido |

No importador atual, `expiry`, `option_type`, `strike`, `type` e `quantity` **não redefinem** o contrato nem a posição. `contract` deve corresponder ao instrumento já conhecido pelas transações.

**Valores em falta:** deixar vazio ou usar `0` nos campos de preço. O modelo CRR calcula cotações teóricas de opções quando faltam preços de opção, usando subjacente e IV fornecida; sem IV, utiliza a hipótese de referência de 35% — **não é IV observada**. A avaliação teórica é indicativa.

**Atenção a bolsas e moedas:** o formulário permite escolher bolsa e ticker do fornecedor; essas preferências são guardadas localmente e **não são atualmente exportadas/importadas por este CSV**. Apesar dos nomes `*_usd`, não inserir preços em GBP como se fossem USD. Para ativos negociados em EUR, a aplicação tem tratamento próprio; confirmar bolsa e moeda antes de usar os resultados.

### Exemplo fictício de cotações

Ver [examples/cotacoes_demo.csv](../examples/cotacoes_demo.csv). O exemplo de cotações está alinhado com os contratos do exemplo de transações, mas deve ser testado após importar primeiro essas transações.

## 3. Limitações e verificação

1. O parser de CSV de transações está dependente de cabeçalhos portugueses da IBKR; outro idioma exige transformação explícita.
2. O dashboard usa FIFO estimado, não substitui extratos oficiais ou contabilidade fiscal.
3. Transações antigas ausentes, eventos societários, exercício e atribuição podem exigir reconciliação.
4. Não confundir lucro realizado com prémios recebidos, nem retorno sobre o prémio com retorno sobre o capital em risco.
5. Verificar manualmente quantidade, direção long/short, moeda, strike, vencimento e total antes de confiar no PnL.

**Privacidade:** nunca colocar CSV reais da conta, identificadores pessoais ou extratos IBKR num repositório público.

## 4. Gerador local yfinance

O script [`tools/aplexd_yfinance.py`](../tools/aplexd_yfinance.py) recebe o CSV de cotações exportado pelo Aplexd (recomendado) ou o histórico de transações IBKR e escreve exatamente as colunas definidas na secção 2. Executar com `python tools/aplexd_yfinance.py entrada.csv -o saida.csv` após instalar `yfinance`.

A consulta de opções é feita por subjacente e data de vencimento, com throttling, cache e limite de chamadas. O script utiliza midpoint de bid/ask positivos, ou último negócio recente quando não existe midpoint válido; não preenche preços ausentes com estimativas. IVs reportadas como decimais são convertidas em percentagem. Sem timestamp de bid/ask verificável, `quote_timestamp_utc` fica vazio.

Atenção: ao importar o CSV gerado, **Cancelar** a opção de limpar os campos previamente preenchidos. O importador preserva preços se o novo campo estiver vazio, mas podem ser atualizados metadados e IVs. Verifica a atualidade dos preços e a moeda antes de utilizar o PnL estimado.
