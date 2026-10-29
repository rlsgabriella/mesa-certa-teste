# Configurações

Nenhum segredo criado neste trabalho fica no repositório nem no JSON exportado
dos workflows.

Exceção conhecida: os dois valores de teste **publicados pelo próprio desafio**
aparecem em arquivos copiados sem alteração. O segredo do HMAC está em
`webhook/README.md` e o token do CRM está em `solucao/crm-mock-teste/crm-mock.py`
(constante `TOKEN`). Não são credenciais reais e foram mantidos para que o
ambiente rode a partir do repositório (decisão registrada no `log-de-decisoes.md`).

## Endereços (não são segredos)

| Item | Valor |
|---|---|
| CRM mock | `http://127.0.0.1:8001` |
| n8n | `http://127.0.0.1:5678` |
| Webhook de teste do n8n | `http://127.0.0.1:5678/webhook-test/mesa-certa/marketing` |
| Webhook de produção do n8n | `http://127.0.0.1:5678/webhook/mesa-certa/marketing` (workflow ativo) |

Use `127.0.0.1`, não `localhost`: no Windows o `localhost` tenta IPv6 primeiro
e cada chamada demora cerca de 2 segundos (`webhook/README.md`).

## Segredos

| Segredo | Onde configurar no n8n |
|---|---|
| Token do CRM (`Authorization: Bearer ...`) | Credencial **Header Auth**: Name `Authorization`, Value `Bearer <token>`. Nos nós HTTP Request: Authentication → Generic Credential Type → Header Auth. |
| Segredo do HMAC do webhook | Ver as duas opções abaixo. |

O n8n exporta o workflow com o nome e o id da credencial, sem o valor.
Por isso o token deve sair do campo "Headers" do nó e ir para a credencial.

### Segredo do HMAC

**Opção A — credencial Crypto do n8n.** Algumas versões do n8n têm uma
credencial "Crypto" com campo de segredo HMAC, usada pelo nó Crypto.
Ainda não verifiquei se a versão instalada (2.8.4) tem essa credencial.

**Opção B — variável de ambiente.** Iniciar o n8n com:

```powershell
$env:WEBHOOK_HMAC_SECRET = "<segredo do webhook/README.md>"
$env:N8N_BLOCK_ENV_ACCESS_IN_NODE = "false"
npx n8n
```

e ler no Code node com `$env.WEBHOOK_HMAC_SECRET`.
Desvantagem: o n8n 2.x bloqueia `$env` por padrão porque, liberado, qualquer
expressão de qualquer workflow enxerga todas as variáveis de ambiente.
Aceitável neste teste local; em produção, preferir a opção A.

`.env.example` lista os nomes das variáveis, sem valores.

## Antes de exportar um workflow

1. Nenhum nó HTTP Request com o token digitado em "Headers".
2. Nenhum Code node com o segredo digitado no código.
3. Depois de exportar, procurar no arquivo pelos valores reais dos segredos.
   Se aparecerem, o arquivo não entra no repositório.
