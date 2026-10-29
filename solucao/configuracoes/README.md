# Configurações

Nenhum segredo criado neste trabalho fica no repositório nem no JSON exportado
dos workflows.

Exceção conhecida: o token de teste do CRM, **publicado pelo próprio desafio**, está
em `solucao/crm-mock-teste/crm-mock.py` (constante `TOKEN`), arquivo copiado sem
alteração. Não é credencial real e foi mantido para que o CRM mock rode a partir do
repositório.

O segredo do HMAC **não** está mais em texto claro: em `webhook/README.md` ele foi
substituído pelo placeholder `<SEGREDO_HMAC_DO_DESAFIO>`. O valor real deve ser lido do
material do desafio e configurado fora do repositório. Ele ainda existe no histórico do
git (commit `2c3ef90`); ver a seção de riscos do `README.md` principal.

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
| Segredo do HMAC do webhook | Variável de ambiente `MESA_CERTA_HMAC_SECRET` no processo do n8n (abaixo). |
| Credencial SQLite | Credencial **SQLite Database account** (`sqliteCredentialsApi`) apontando para o `mesa_certa.db` de trabalho. |

O n8n exporta o workflow com o nome e o id da credencial, sem o valor.
Por isso o token deve sair do campo "Headers" do nó e ir para a credencial.

### Segredo do HMAC (usado nos testes aprovados)

O workflow 01 lê o segredo com `$env.MESA_CERTA_HMAC_SECRET`. Iniciar o n8n com
as três variáveis abaixo (o valor vem do material do desafio):

```powershell
$env:MESA_CERTA_HMAC_SECRET = "<segredo do desafio>"
$env:N8N_BLOCK_ENV_ACCESS_IN_NODE = "false"
$env:NODE_FUNCTION_ALLOW_BUILTIN = "crypto"
npx n8n
```

- `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`: o n8n 2.x bloqueia `$env` por padrão.
- `NODE_FUNCTION_ALLOW_BUILTIN=crypto`: sem isso o Code node falha com
  `Module 'crypto' is disallowed` (erro visto na execução 352).
- Desvantagem: com `$env` liberado, qualquer expressão de qualquer workflow enxerga
  todas as variáveis de ambiente. Aceitável neste teste local; em produção, preferir
  uma credencial própria do n8n.
- O Code node escreve no log o fingerprint SHA-256 do segredo (`console.log`). Não é o
  segredo, mas convém remover essa linha antes de uso fora do teste.

`.env.example` lista os nomes das variáveis, sem valores. Para o script de teste
`solucao/testar_webhook_hmac.py`, defina `MESA_CERTA_HMAC_SECRET` na sessão do terminal.

## Antes de exportar um workflow

1. Nenhum nó HTTP Request com o token digitado em "Headers".
2. Nenhum Code node com o segredo digitado no código.
3. Depois de exportar, procurar no arquivo pelos valores reais dos segredos.
   Se aparecerem, o arquivo não entra no repositório.
