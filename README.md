# Aplexd

**Alieno periculo lucrum · Ex disciplina**

Aplexd é um journal interativo de investimento para analisar transações da Interactive Brokers (IBKR), posições em aberto, opções e rentabilidade.

## Executar

O dashboard é um ficheiro HTML autónomo. Abre `index.html` no browser ou acede ao GitHub Pages, após publicação.

1. Escolhe **Importar CSV de transações** e seleciona um export de **Histórico de transações** da IBKR.
2. Consulta a grelha de posições abertas e preenche as cotações do subjacente e de cada opção.
3. Podes importar/exportar as cotações em CSV para manutenção no Excel.
4. Explora resultados, posições e timeline. As opções vencidas sem transação de fecho são marcadas com uma nota numerada e tratadas como valores provisórios.

**Privacidade:** Não publiques extratos da conta, carteiras reais, cotações pessoais nem ficheiros contendo identificadores de conta neste repositório público. Os ficheiros importados são processados localmente no navegador. A funcionalidade opcional de obtenção de preços públicos faz pedidos a serviços externos para os símbolos consultados.

**Precisão:** os cálculos são estimativas e não substituem o extrato oficial da corretora. Atribuições, operações societárias, posições anteriores ao período importado e estratégias com múltiplas pernas podem precisar de reconciliação. As cotações teóricas de opções não são preços executáveis.

## Formatos CSV e integração com LLMs

O Aplexd recebe **dois CSV distintos**:

- [Especificação CSV v1](docs/CSV_FORMAT.md) — campos, formatos, sinais, datas, opções, moedas e limitações do importador.
- [Guia para LLMs](docs/LLM_GUIDE.md) — instruções para gerar ficheiros compatíveis sem inventar dados.
- [Exemplo fictício de transações](examples/transacoes_demo.csv).
- [Exemplo fictício de cotações](examples/cotacoes_demo.csv).

**Ordem de utilização:** importa primeiro as transações e depois as cotações. O segundo ficheiro não abre nem fecha posições; os identificadores de contratos devem corresponder aos das transações. O exemplo de cotações inclui também um contrato já fechado, apenas para ilustrar o formato — não aparecerá entre as posições abertas.

## Atualizar cotações com yfinance (Python local)

O utilitário [`tools/aplexd_yfinance.py`](tools/aplexd_yfinance.py) consulta cadeias de opções do Yahoo Finance via `yfinance` e produz um CSV compatível com **Importar cotações**. Não usa a conta IBKR nem consome créditos da MarketData.app.

Requer Python 3.10+:

```bash
python -m pip install yfinance
python tools/aplexd_yfinance.py "cotacoes_exportadas.csv" -o "cotacoes_atualizadas.csv"
```

**Fluxo preferido:** importar as transações no Aplexd → **Exportar cotações CSV** → executar o script com o ficheiro exportado → **Importar cotações** e escolher **Cancelar** quando perguntar se deve limpar os campos existentes. Em alternativa, o script aceita diretamente um histórico de transações IBKR em português, mas a reconstrução de posições por somatório de quantidades pode não refletir corretamente atribuições e eventos societários.

Para aplicar limites mais conservadores:

```bash
python tools/aplexd_yfinance.py "cotacoes_exportadas.csv" -o "cotacoes_atualizadas.csv" --delay 5 --cache-hours 12 --max-requests 20
```

Para instrumentos em bolsas específicas, `--ticker SGLD=SGLD.L` permite identificar o símbolo Yahoo. **Atenção:** o script deixa preços de bolsas com moedas potencialmente diferentes de USD em branco; verifica moeda e bolsa manualmente no Aplexd.

**Proteção de símbolos e preços:** o mesmo ticker pode representar instrumentos distintos em bolsas diferentes (por exemplo, um ETF em Londres e uma ação nos EUA). Confirma o símbolo Yahoo com `--ticker ORIGEM=DESTINO` e a moeda do instrumento. O script rejeita diferenças superiores a 50% face ao preço de referência do CSV, e o importador pede confirmação antes de sobrepor preços que variem mais de 50%. Estes controlos não substituem uma validação da identidade do ativo. **Se uma cotação incorreta já tiver sido importada, corrige-a manualmente antes de voltar a importar.**

A cache fica na pasta `.aplexd_yahoo_cache` junto do ficheiro de saída. Não publiques dados da carteira, ficheiros gerados ou cache no repositório. Os dados Yahoo são não oficiais e podem estar atrasados, incompletos ou sujeitos a bloqueios; `--delay` e cache mitigam pedidos repetidos, mas não garantem disponibilidade. A data do último negócio não é a data da cotação bid/ask; o script deixa o timestamp vazio quando usa midpoint.

## Publicar no GitHub Pages

1. Coloca o dashboard completo na raiz do repositório com o nome `index.html`.
2. Abre **Settings → Pages**.
3. Em **Build and deployment**, escolhe **Deploy from a branch**, branch `main`, pasta `/(root)`, e **Save**.
4. URL prevista: https://primeiraacademiadev.github.io/Aplexd/

## Princípios

- Separar negócios encerrados de posições vivas.
- Preservar o histórico, mas destacar resultados estimados e pendentes de reconciliação.
- Distinguir PnL realizado, PnL latente, rentabilidade percentual e capital efetivamente comprometido.
- Nunca introduzir dados privados como amostra da aplicação.

Projeto experimental, sem aconselhamento financeiro.
