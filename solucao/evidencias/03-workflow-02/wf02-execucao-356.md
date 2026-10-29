# Workflow 02 (corrigido v2): execução 356, APROVADA

Execução manual única em 29/10/2026, iniciada às 16:17:07 UTC (13:17:07 em Brasília) e concluída em 0,8 s.
Workflow: `Mesa Certa|02-Conciliação Marketing × CRM (corrigido v2)`, id `fcMKsKzpcdAMKnr0`,
12 nós, importado de `solucao/workflows/corrigidos/Mesa Certa_02-Conciliacao Marketing x CRM.importar.json`.
O workflow original (`tTDsv01lkDZqTnp1`) não foi tocado.

Verificação prévia (antes de executar): exatamente 1 evento pendente comercial
(`evt_t1_comercial_005`), CRM com 395 negócios, credenciais `rmoFJ2XC21kBrCVT` (CRM)
e `A6Zo3HG9VmdtVFOr` (SQLite) ligadas aos nós.

## Resultado

| Item | Resultado |
|---|---|
| Execução | id **356**, status **success** |
| Lead processado | só `evt_t1_comercial_005` (1 item em "Buscar Leads Pendentes") |
| Negócio localizado pelo e-mail | sim: `GET /deals?email=t1.comercial.005@…` devolveu `total: 1`, `deal_id` **20395**, etapa Novo |
| "Negócio existe?" | ramo verdadeiro |
| "Vincular Negócio Existente" | executou: `changes: 1` |
| "Criar negócio ausente." (POST) | **não executou** (nenhuma chamada de criação) |
| `sync_eventos` do evento 005 | de `pendente` / `deal_id NULL` para **`sincronizado` / `deal_id 20395`**, `tentativas 0`, `ultimo_erro NULL`, `atualizado_em 2026-10-29 16:17:07` (UTC) |
| `sync_eventos` geral | 4 sincronizados, 0 pendentes |
| CRM | **395 negócios** antes e depois (Novo 110); 1 único negócio com o e-mail do 005; maior `deal_id` continua 20395 |

Nós do ramo de erro (Verificar criação após erro, Negócio criado após erro?, Confirmar
Sincronização após Erro, Marcar Falha de Sincronização) e "Atualizar SQLite." não rodaram,
como esperado neste caminho.

## Observações

- Isto fecha a pendência do T1.005: o Workflow 01 cria o negócio e deixa o evento `pendente`;
  o Workflow 02 conciliou o evento e o marcou `sincronizado` sem criar outro negócio.
- Não foi exercitado o caminho em que o WF02 cria o negócio (POST) nem o tratamento de erro
  do CRM (429/500). Estes caminhos seguem sem evidência de execução.
- `atualizado_em` gravado pelo WF02 usa `datetime('now')` (UTC, `AAAA-MM-DD HH:MM:SS`), enquanto
  o WF01 grava ISO com `Z`.

Dados estruturados: `wf02-execucao-356.json`.
