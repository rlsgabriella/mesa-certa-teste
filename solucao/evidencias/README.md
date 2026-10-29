# Evidências

## Teste de ponta a ponta: João Almeida (`evt_500110`)

Evento do lote enviado ao webhook do n8n em 28/10/2026. O workflow validou a
assinatura, consultou o CRM, criou o negócio e, na consulta seguinte, encontrou o
negócio já existente.

| Arquivo | O que mostra |
|---|---|
| `post.png` | Nó HTTP Request (POST `/deals`) devolvendo `{"status": "ok", "deal_id": 20392}`. |
| `get.png` | Nó "Consultar Lead no CRM" (GET `/deals?email=...`) devolvendo o negócio 20392, `total: 1`. |
| `lead.png` | Nó "Lead Não Existe?" com `total = 1`: o evento vai para o ramo falso e não cria outro negócio. |
| `crm-estado-teste-joao-almeida-20392.json` | Estado salvo pelo CRM mock depois do teste. |

A descrição dos três prints segue as telas do n8n enviadas na conversa de
28/10 e os nomes dos arquivos. Conferir abrindo cada imagem antes da entrega.

### Estado de teste × estado inicial do CRM

| | Estado inicial | Estado de teste (este arquivo) |
|---|---|---|
| Arquivo | `crm-mock-teste/crm-seed.json` | `evidencias/crm-estado-teste-joao-almeida-20392.json` |
| Negócios | 391 | 392 |
| Negócio 20392 | não existe | João Almeida, etapa Novo, criado em 2026-10-28 00:33:11 (Brasília) |

O arquivo de teste é uma cópia de
`Downloads\candidato\candidato\solucao\crm-mock-teste\crm-mock-estado.json`
(SHA-256 `A5A5BE4D4FD228054BB8879454A65CCFB7E0115D4EB8EDFD41A1B831AF6CFDEC`),
o CRM que estava rodando durante o teste. Se esse CRM for reiniciado com
`--reset`, o original volta para 391 negócios; esta cópia continua guardando a prova.

O print `post.png` mostra o token do CRM digitado no nó HTTP Request. É o token
de teste publicado no `crm-mock/README.md` do desafio, não uma credencial real.

## Auditoria

`auditoria-2026-10-28.md`: integridade dos bancos e números do lote e do CRM,
separando números confirmados de hipóteses.
