# T1.005 — Lead comercial com HMAC válido (Workflow 01): APROVADO

Data do teste: 29/10/2026 (execução n8n iniciada às 14:33:02 UTC).
Workflow: `Mesa Certa | 01 - Recebimento e Cadastro de Leads` (`bZu7Ku16BbgSj504`),
versão `88e7d88f-28c2-4345-b60b-33b98d53b4c1`, com os 4 nós SQLite do tipo
`n8n-nodes-sqlite3.sqliteNode`.

## Envio

Um único envio, sem retry, por `solucao/testar_webhook_hmac.py` para
`http://127.0.0.1:5678/webhook-test/mesa-certa/marketing`.

| Campo | Valor |
|---|---|
| `event_id` | `evt_t1_comercial_005` |
| e-mail | `t1.comercial.005@teste-mesacerta.example` |
| mensagem | "Quero uma demonstracao do sistema e conhecer os planos." |
| corpo | 302 bytes |
| `X-Signature` | `sha256=47181ba53d1e39f98792c5e62660431648499084969e617ff7c013a9e5324d9b` |
| HTTP recebido | **200** |
| resposta | `{"status":"recebido","mensagem":"Evento registrado para sincronizacao"}` |

O segredo HMAC veio de variável de ambiente carregada do `.env` (ignorado pelo git)
durante o envio e não aparece nesta evidência.

## Execução no n8n: id 355, status `success`

Duração de 9,5 s. Os 12 nós do caminho comercial executaram sem erro.

| Nó | Resultado |
|---|---|
| Validar Assinatura HMAC | `assinatura_valida: true`, `ASSINATURA VALIDADA` |
| Assinatura Válida? | ramo verdadeiro |
| Classificar Pedido | `classificacao: "comercial"` |
| Verificar evento (SQLite) | `total_encontrado: 0` |
| Evento Ainda Não Registrado? | ramo "registrar" |
| Registrar pedido (SQLite) | `changes: 1`, `lastInsertRowid: 105` |
| Persistir evento (SQLite) | `changes: 1`, `lastInsertRowid: 4` |
| Responder Recebimento HTTP 200 | executou |
| Pedido é comercial? | ramo "comercial" |
| Consultar Lead no CRM | `total: 0` |
| Lead Não Existe? | ramo "criar" |
| Criar Negócio no CRM | `status: ok`, `deal_id: 20395` |

## SQLite (`mesa_certa.db`, leitura independente)

- `pedidos_formulario`: 1 linha, `id` 105, `classificacao = comercial`,
  `recebido_em = 2026-10-29T14:33:03.601Z`.
- `sync_eventos`: 1 linha, `estado_sync = pendente`, `deal_id = NULL`,
  `tentativas = 0`, `ultimo_erro = NULL`.

## CRM (CRM mock, porta 8001)

| | Antes | Depois |
|---|---|---|
| Total de negócios | 394 | **395** |
| Etapa "Novo" | 109 | **110** |
| Demais etapas | Contato 133, Perdido 72, Reunião marcada 43, Reunião realizada 37 | inalteradas |

Negócio criado (conferido no arquivo de estado do mock, 1 negócio com esse e-mail):
`deal_id 20395`, "T1 Comercial Cinco", restaurante "Restaurante Boa Mesa",
origem "site", etapa **Novo**, criado em 2026-10-29 11:33:12 (Brasília).

## Pendência registrada

O Workflow 01 criou o negócio 20395 no CRM, mas **não atualizou `sync_eventos`**:
a linha continua `pendente`, sem `deal_id`. Não há nó depois de "Criar Negócio no
CRM". Essa atualização precisa vir do Workflow 02 (conciliação) ou de um nó novo no
Workflow 01. Ver a análise do Workflow 02 em `log-de-decisoes.md` (entrada
"T1.005").

## Não coberto por este teste

- Deduplicação por reenvio do mesmo `event_id`.
- Lead de suporte/não comercial (não deve criar negócio).
- Assinatura inválida (HTTP 401).
- Os 4 nós SQLite antigos (`CUSTOM.sqliteNode`) estavam no workflow, desconectados, durante este
  teste. Foram removidos no editor logo depois (14:33:29 UTC); o export final tem 18 nós.

Dados estruturados: `t1-005-resultado.json`.
