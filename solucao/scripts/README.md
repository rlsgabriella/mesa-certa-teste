# Scripts de indicadores (resumo semanal da gestora)

Calculam os números que a gestora pediu (funil, pedidos da semana, pedidos que não chegaram ao CRM,
prazo de primeiro contato e quem está sem retorno) e montam um resumo em linguagem simples.

| Arquivo | Para quê |
|---|---|
| `resumo_semanal.py` | Calcula os indicadores. Só lê o SQLite (`mode=ro`). Gera JSON e texto, ou sobe um serviço local para o n8n. |
| `test_resumo_semanal.py` | 25 testes automáticos com bancos temporários (horas úteis, classificação, funil, prazo, somente leitura). |
| `validar_resumo_historico.py` | Roda o cálculo sobre uma **cópia** de `mesa_certa.original.db` para 12/10/2026 08:00 e compara com a apuração histórica. |

Só usa a biblioteca padrão do Python 3.10 ou mais novo. Não grava no banco, não chama o CRM, não dispara webhook.

## Como usar

```powershell
# resumo da semana anterior a uma data (horário de Brasília); sem --ref usa "agora"
py solucao\scripts\resumo_semanal.py --ref "2026-10-12 08:00" --saida texto

# reproduzir 12/10/2026 com o lote do webhook (o banco só tem pedidos até 04/10)
$env:MESA_CERTA_HMAC_SECRET = "<segredo do desafio>"      # só para conferir as assinaturas do lote
py solucao\scripts\resumo_semanal.py --db mesa_certa.original.db --lote webhook\lote-webhook.jsonl `
   --ref "2026-10-12 08:00" --json-out resumo.json --txt-out resumo.txt --saida nenhuma

# testes e validação histórica (na raiz do repositório)
py -m unittest solucao/scripts/test_resumo_semanal.py -v
py solucao\scripts\validar_resumo_historico.py --saida-dir solucao\evidencias\04-workflow-03
```

Parâmetros: `--db`, `--lote`, `--segredo-env`, `--ref`, `--inicio`, `--fim`, `--json-out`, `--txt-out`,
`--saida {json,texto,nenhuma}`, `--servir`, `--porta`. O período padrão é a semana completa anterior à semana da
referência (segunda 00:00 até a segunda seguinte 00:00). Datas e horas em horário de Brasília (UTC-3, sem horário de
verão); `pedidos_formulario.criado_em` e o lote estão em UTC e são convertidos.

## O que sai (JSON)

| Seção | Conteúdo |
|---|---|
| `indicadores_comprovados` | Leitura direta dos dados: funil por etapa, negócios criados e atualizados, prazo de primeiro contato de **todos** os negócios criados, negócios em Novo sem contato e com prazo vencido. |
| `estimativas` | Dependem da regra de classificação por texto e do cruzamento por e-mail/telefone: pedidos comerciais, ausentes no CRM, pessoas distintas, prazo só dos pedidos comerciais, quem cobrar hoje. |
| `dados_incompletos` | O que falta nos dados desta execução (assinatura não conferida, pedidos que terminam antes do fim da semana, banco do CRM desatualizado, contatos depois da referência...). |
| `limitacoes` | O que os dados não permitem afirmar (autor do contato, feriados, regra de classificação não validada...). |
| `resumo_texto` | O texto para a gestora. |

## Definições usadas

- **Funil na referência:** última etapa do `historico_etapas` até a referência, só para negócios criados até ela.
- **Atualizados:** `atualizado_em` dentro do período. É a definição que reproduz a planilha da gestora (187 em 05 a 11/10);
  **não** conta pedidos.
- **Pedido comercial:** regra por texto, nome e e-mail (`classificar_pedido`). "Quero testar o sistema" é comercial.
- **Sem correspondência:** pedido comercial sem negócio com o mesmo e-mail ou telefone (normalizados) criado a partir de
  60 s antes do pedido. Se só há negócio mais antigo, conta como "pessoa já tinha negócio".
- **Prazo:** horas úteis (seg a sex, 8h às 18h) entre `criado_em` e `primeiro_contato_em`. Limite de 4 h.
  "Sem retorno e vencido": sem contato e mais de 4 h úteis desde a criação até a referência (Perdido fica fora).
- **Mediana/percentil 90:** mediana estatística; percentil na posição `int(0,9 x n)`.

## Validação (referência 12/10/2026 08:00)

`validar_resumo_historico.py`: **23 de 23 indicadores conferem** com a apuração histórica (funil 391, 187 atualizados,
142 criados, 136 pedidos comerciais, 12 sem correspondência, 68 sem retorno vencido e mais 17 números de apoio).
O banco original e a cópia ficaram idênticos (SHA-256 igual antes e depois). Relatório e saídas:
`solucao/evidencias/04-workflow-03/validacao-resumo-semanal-2026-10-12.md`, `resumo-semanal-2026-10-12.json` e `.txt`.
Única diferença de definição: a mediana de horas úteis é 2,08 aqui (média dos dois valores centrais) e 2,15 na apuração
anterior (valor central superior).

Rodar contra o `mesa_certa.db` de trabalho com `--ref "2026-10-12 08:00"` dá o mesmo funil, 142, 187 e 68, porque
negócios criados depois da referência são ignorados. Mas o `pedidos_formulario` de trabalho contém `evt_500110`
repetido do teste de 28/10, então os pedidos só batem com o lote usando a **cópia do original**.

## Serviço local para o n8n

O nó Execute Command vem desativado no n8n 2.x, então o n8n chama um serviço HTTP local, somente leitura:

```powershell
py solucao\scripts\resumo_semanal.py --servir --porta 8002 --db mesa_certa.db
```

- `GET /saude` e `GET /resumo?ref=AAAA-MM-DDTHH:MM`. Escuta só em `127.0.0.1`; qualquer outro método responde 501.
- Para ficar sempre no ar é preciso registrá-lo como tarefa do Windows (não feito).

## Workflow 03 (importado, executado à mão, não ativado)

`solucao/workflows/wf03-resumo-semanal.json`: Schedule Trigger `0 8 * * 1` com `settings.timezone = America/Sao_Paulo`, chamada ao serviço
(2 tentativas), composição do resumo, envio por e-mail **somente se** `RESUMO_SEMANAL_DESTINATARIO` estiver definida,
e registro de falhas (nó de parada com erro, que aparece na lista de execuções do n8n).

Estado verificado no n8n em 29/10 às 16:27 (leitura pelo MCP): workflow `wrGCERjaPYAeDcuH`, `active: false`, sem versão publicada.
Execuções, todas `manual`: **357** (14:53, sucesso, e-mail aceito), 358 (14:56, cancelada), **359** (16:19, sucesso, e-mail aceito) e 360 (16:19, só o gatilho).
Nenhuma execução agendada. A cópia importada não tem `timezone` em `settings`; a execução 360 mostra o gatilho no fuso `America/New_York`.
Então um cron como `20 16 * * *` dispararia às 16:20 de Nova York (17:20 em Brasília), e a segunda às 08:00 sairia às 09:00 em Brasília.
Correção a fazer na interface: Settings do workflow, Timezone `America/Sao_Paulo`.

### O que falta para ativar o envio automático

1. **Dados atualizados.** O `negocios_crm` do SQLite é uma cópia do CRM tirada em 12/10 (últimos registros em 11/10).
   Nenhum workflow a atualiza, e o CRM mock já tem negócios que a cópia não tem. Sem uma atualização antes de
   segunda 08:00, o resumo avisa "banco desatualizado" e mostra números velhos.
2. **Serviço no ar** na porta 8002 com o `mesa_certa.db` de trabalho (tarefa do Windows ou outro meio).
3. **Credencial SMTP** (ou Slack) criada no n8n e escolhida no nó "Enviar e-mail"; o JSON não traz credencial.
4. **Variáveis no processo do n8n:** `RESUMO_SEMANAL_DESTINATARIO` e `RESUMO_SEMANAL_REMETENTE` (valores reais, a definir pela
   gestora/time) e `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` (já usada no projeto).
5. **Importar e ativar** o workflow (só depois de testar com envio de teste) e manter o n8n ligado na segunda às 08:00.
6. **Decisão:** canal (e-mail ou Slack) e quem recebe.
