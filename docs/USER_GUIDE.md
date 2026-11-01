# Aplexd — Guia de utilização assistida por LLM

**Versão de referência da aplicação:** 2026.11.01.22. Consultar `version.json` e `index.html` para confirmar alterações futuras.

Este guia orienta um utilizador desde a primeira visita até à leitura crítica do PnL. Utiliza também [CSV_FORMAT.md](CSV_FORMAT.md) e [LLM_GUIDE.md](LLM_GUIDE.md) para tarefas de conversão de ficheiros.

## Instruções para o LLM orientador

- Responder na língua do utilizador, preferindo português de Portugal quando apropriado.
- Dar instruções curtas, por etapas, baseadas nos comandos existentes na versão atual. Não afirmar que se clicou, importou ou consultou algo sem confirmação.
- Não pedir tokens da MarketData.app, palavras-passe, credenciais IBKR nem extratos com identificadores pessoais no chat público ou no repositório. O utilizador pode guardar o token cifrado no browser através do fluxo próprio.
- Nunca inferir que PnL estimado é PnL oficial. Não inventar preços, transações, taxas de câmbio ou datas. Identificar limitações do FIFO e cotações teóricas.
- Para falhas de cotação, começar pelo diagnóstico local; evitar gastos de créditos e chamadas repetidas a serviços externos.
- Relembrar que a app corre no browser do utilizador; o script `yfinance` é local e independente.

## 1. Abrir a aplicação

Endereço: https://primeiraacademiadev.github.io/Aplexd/

No desktop, a estreita faixa lateral esquerda com chevron abre as **Operações**; clicar novamente fecha-a. No telemóvel, deslizar da margem esquerda para a direita abre a barra e deslizar para a esquerda fecha-a. As operações estão agrupadas em **Ficheiros**, **Dados de mercado** e **Aplicação**.

A parte superior tem o seletor de apresentação: **Valores e percentagens** ou **Apenas percentagens**. O modo percentual da timeline usa o capital identificável como denominador, que pode ser parcial; não é uma rentabilidade ponderada pelo tempo.

## 2. Importar transações

1. Na barra lateral, escolher **Ficheiros → Importar CSV de transações**.
2. Selecionar um histórico de transações IBKR em português, no formato descrito em [CSV_FORMAT.md](CSV_FORMAT.md).
3. Confirmar na secção **Fonte de dados** que deixou de indicar a demonstração fictícia; verificar número de registos e posições.
4. Se falhar, inspecionar a consola do browser (F12 → Console), filtrando por `[Aplexd]`. Não publicar o extrato em GitHub.

Também existe a opção **Carregar demo fictícia**, útil para aprendizagem sem dados de uma conta real.

## 3. Atualizar cotações e IV

As ações e opções podem ter cotações de fontes ou datas diferentes. As opções podem ser valorizadas pelo modelo CRR quando não existem cotações de mercado; isso não representa um preço negociável.

**Via aplicação:** barra lateral → **Dados de mercado → Consultar preços públicos** (subjacentes), **Consultar opções e IV** (MarketData.app, com token pessoal opcional), ou **Diagnosticar preços** (auditoria local, sem chamadas externas). A MarketData.app tem limites de créditos.

**Via Python local, sem créditos MarketData.app (preferido para muitas posições):**

1. Na barra lateral → **Ficheiros → Exportar cotações CSV**.
2. Guardar o CSV exportado na pasta privada `.quotes/` da cópia local do repositório.
3. Instalar `yfinance` no Python do projeto: `python -m pip install yfinance` ou, no Windows, `.venv\\Scripts\\python.exe -m pip install yfinance`.
4. Executar `run.bat` no Windows ou `sh run.sh` no Linux/macOS.
5. Selecionar o CSV listado. O resultado é `nome.out.csv`, na mesma pasta. A cache evita pedidos desnecessários e os parâmetros `--delay` e `--max-requests` controlam pedidos do script, não garantem limites internos Yahoo.
6. Na aplicação, **Ficheiros → Importar cotações** e selecionar `nome.out.csv`. Quando surgir a pergunta sobre limpar cotações anteriores, escolher **Cancelar** para conservar os valores existentes e sobrepor apenas campos preenchidos.

**Controlo de qualidade:** comparar a moeda, a bolsa, os timestamps, as IVs e os preços. Tickers iguais podem identificar instrumentos diferentes (ex.: SGLD). Se necessário, executar o script com `--ticker SGLD=SGLD.L`, após confirmar a identidade e a moeda do instrumento. O programa alerta para mudanças superiores a 50%, mas isso não substitui a verificação.

## 4. Interpretar os resultados

- **PnL realizado estimado:** resultados atribuídos a negócios fechados por FIFO e eventos presumidos, sujeitos a reconciliação.
- **Dividendos/retenções:** componente separada de rendimentos.
- **PnL latente:** valorização das posições ainda abertas, com preços de mercado, importados ou teóricos.
- **PnL total estimado:** realizado + dividendos/retenções + latente. Pode ser parcial quando faltam cotações.
- **Resultados por símbolo:** gráfico ordenável alfabeticamente (A–Z, Z–A) ou por contribuição realizada crescente/decrescente.
- **Evolução do PnL no tempo:** acumulado do realizado e rendimentos, incluindo perdas e vencimentos presumidos; **não** é uma curva de equity diária porque não incorpora PnL latente histórico. Respeita o seletor de apresentação percentual com limitações de base de capital.

A secção **Cotações necessárias para as posições abertas** encontra-se no fim da página. Permite rever preços, IV e parâmetros por contrato.

## 5. Diagnóstico seguro

1. Comparar o PnL total estimado com o resultado oficial da corretora, sem misturar a variação diária com o resultado acumulado desde os depósitos.
2. Abrir **Dados de mercado → Diagnosticar preços** e verificar na consola as fontes, as datas e os valores por contrato. Esta operação não consome créditos.
3. Verificar primeiro erros de identidade/bolsa/moeda, depois preços antigos, diferenças bid/ask/last e só depois possíveis diferenças de custo contabilístico.
4. Não tratar opções marcadas como `TEORICO` como se tivessem cotação observada.
5. Para problemas com o gerador local, registar mensagem de erro e versão do `yfinance`, sem incluir tokens ou extratos privados.

## 6. Pedido pronto a fornecer a outro LLM

> És um assistente de utilização do Aplexd. Consulta primeiro o README.md, docs/USER_GUIDE.md, docs/CSV_FORMAT.md e docs/LLM_GUIDE.md deste repositório, confirmando a versão em version.json. Guia-me passo a passo para importar transações, atualizar preços de opções com o script local e interpretar o PnL. Distingue sempre resultados realizados, latentes e estimados; não inventes valores nem me peças palavras-passe ou tokens. Se houver erros, faz diagnóstico local antes de sugerir novas consultas pagas.
