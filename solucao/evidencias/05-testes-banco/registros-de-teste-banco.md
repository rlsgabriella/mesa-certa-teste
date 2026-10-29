# Registros criados pelos testes em `mesa_certa.db`

`mesa_certa.original.db` está intacto (SHA-256 `F545271F6CC9C8761188FE5275DF1BD878ED63E74965EF77642EDA37419540D6`,
sem diferença em relação ao commit `2c3ef90`). `mesa_certa.db` é o banco de trabalho: tudo abaixo
foi criado nele pelos testes e pelos workflows. Levantamento feito em 29/10/2026, comparando os dois
arquivos em modo somente leitura.

## Mudanças de estrutura em relação ao original

| Item | Original | Trabalho |
|---|---|---|
| Tabela `sync_eventos` | não existe | existe (estado de sincronização por `event_id`) |
| Coluna `pedidos_formulario.classificacao` | não existe | existe (`comercial`, `nao_classificado`, ...) |
| `historico_etapas` | 879 linhas | 879 (igual) |
| `negocios_crm` | 391 linhas | 391 (igual) |
| `pedidos_formulario` | 100 linhas | 105 linhas |
| `sync_eventos` | | 4 linhas |

## Linhas de teste em `pedidos_formulario` (ids 101 a 105)

| id | `event_id` | Origem | `classificacao` |
|---|---|---|---|
| 101 | `evt_500110` | Evento do lote (João Almeida), 28/10 | `nao_classificado` |
| 102 | `teste-hmac-valido-001` | Teste de HMAC válido, 28/10 | `nao_classificado` |
| 103 | `teste-hmac-valido-002` | Teste de HMAC válido, 28/10 | `nao_classificado` |
| 104 | `teste-reconciliacao-003` | Teste de conciliação, 29/10 | `nao_classificado` |
| 105 | `evt_t1_comercial_005` | **T1.005**, execução 355, 29/10 | `comercial` |

As 104 primeiras linhas estão `nao_classificado` porque a coluna `classificacao` foi criada depois;
não foram reclassificadas (decisão registrada no `log-de-decisoes.md`).

## Linhas em `sync_eventos`

| `event_id` | `estado_sync` | `deal_id` | Como chegou lá |
|---|---|---|---|
| `teste-hmac-valido-001` | `sincronizado` | 20393 | teste manual |
| `teste-hmac-valido-002` | `sincronizado` | 20392 | teste manual |
| `teste-reconciliacao-003` | `sincronizado` | 20394 | teste de conciliação |
| `evt_t1_comercial_005` | `sincronizado` | 20395 | WF01 criou o evento `pendente` (execução 355); WF02 marcou `sincronizado` (execução 356, 16:17:07 UTC) |

## Negócios de teste no CRM mock (fora do banco)

Negócios 20392 a 20395 (CRM de 391 para 395). O CRM mock guarda o estado em
`solucao/crm-mock-teste/crm-mock-estado.json`, ignorado pelo git; `py crm-mock.py --reset`
volta aos 391 negócios do `crm-seed.json`. Cópia do estado do primeiro teste:
`../02-workflow-01/crm-estado-teste-joao-almeida-20392.json`.

## Como voltar ao estado inicial

1. Copiar `mesa_certa.original.db` por cima de `mesa_certa.db`.
2. Rodar o CRM mock com `--reset`.
