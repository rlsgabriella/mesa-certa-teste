# Webhook do formulário

O formulário do site da Mesa Certa entrega cada pedido de demonstração por webhook (HTTP POST) a um endereço que você define. Você precisa subir o receptor e gravar o que chega no banco.

## O que chega

`POST` com corpo JSON (UTF-8):

| Campo | Exemplo | Observação |
|---|---|---|
| `event_id` | `evt_500123` | identifica o evento |
| `criado_em` | `2026-10-06T14:03:22Z` | horário em UTC |
| `nome` | `Maria Souza` | |
| `email` | `maria.souza@gmail.com` | |
| `telefone` | `(11) 98765-4321` | o formato varia |
| `restaurante` | `Pizzaria Bella Massa` | |
| `mensagem` | `Quero conhecer o sistema...` | texto livre do campo "o que você precisa?" |
| `origem` | `site` | |

Cabeçalho `X-Signature`: `sha256=` seguido do HMAC-SHA256 do corpo bruto, usando o segredo compartilhado `<SEGREDO_HMAC_DO_DESAFIO>`.

## O que o remetente espera de você

- Responda **2xx** quando o evento estiver recebido.
- Se a resposta for **5xx**, der erro de conexão ou demorar mais de **5 segundos**, o remetente envia o mesmo evento de novo (até 4 tentativas no total).
- Se a resposta for **4xx**, o remetente entende que o evento está errado e não reenvia.

## Como testar

1. Suba o seu receptor (qualquer linguagem ou ferramenta) escutando em `http://127.0.0.1:8000/webhook`.
2. Rode: `python enviar-lote.py`
3. O lote cobre os eventos emitidos de **05/10 às 00:00 UTC até 12/10 às 00:00 UTC**.

Opções: `--url` (outro endereço), `--limite 20` (só as primeiras entregas, para testar), `--ritmo 0.1` (pausa entre entregas, em segundos).

O remetente grava `envios.log` com cada tentativa. Para repetir o lote do zero, restaure o banco (veja o enunciado) e rode de novo.

Use `127.0.0.1` e não `localhost`: no Windows o `localhost` tenta IPv6 primeiro e cada entrega demora cerca de 2 segundos.

---

> Nota da entrega: o valor do segredo HMAC foi substituído por `<SEGREDO_HMAC_DO_DESAFIO>`
> para não ficar em texto claro neste repositório. O valor real vem do material do desafio
> e, nos testes, é configurado fora do repositório na variável `MESA_CERTA_HMAC_SECRET`
> (ver `solucao/configuracoes/README.md`). Este é o único ponto em que este arquivo difere
> do original do desafio.
