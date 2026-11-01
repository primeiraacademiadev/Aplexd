# Aplexd

**Alieno periculo lucrum · Ex disciplina**

Aplexd é um journal interativo de investimento para analisar transações da Interactive Brokers (IBKR), posições em aberto, opções e rentabilidade.

## Executar

O dashboard é um ficheiro HTML autónomo. Abre `index.html` no browser ou acede ao GitHub Pages, após publicação.

1. Escolhe **Importar CSV de transações** e seleciona um export de **Histórico de transações** da IBKR.
2. Consulta a grelha de posições abertas e preenche as cotações do subjacente e de cada opção.
3. Podes importar/exportar as cotações em CSV para manutenção no Excel.
4. Explora resultados, posições e timeline. As opções vencidas sem transação de fecho são marcadas com `*` e tratadas como valores provisórios.

**Privacidade:** Não publiques extratos da conta, carteiras reais, cotações pessoais nem ficheiros contendo identificadores de conta neste repositório público. Os ficheiros importados são processados localmente no navegador. A funcionalidade opcional de obtenção de preços públicos faz pedidos a serviços externos para os símbolos consultados.

**Precisão:** os cálculos são estimativas e não substituem o extrato oficial da corretora. Atribuições, operações societárias, posições anteriores ao período importado e estratégias com múltiplas pernas podem precisar de reconciliação. As cotações teóricas de opções não são preços executáveis.

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
