# Solução — automações em n8n

A solução roda em n8n. Cada automação é um workflow exportado em JSON na pasta
`workflows/`. O Python fica só para subir o CRM mock fornecido pelo desafio.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `workflows/` | Exports finais dos workflows 01 e 02, exportados da instância n8n em 29/10/2026, e as regras de negócio que cada um implementa (`workflows/README.md`). |
| `configuracoes/` | Endereços, como configurar credenciais no n8n e `.env.example` sem valores. |
| `evidencias/` | Índice (`evidencias/README.md`) e subpastas por tema: `01-auditoria`, `02-workflow-01`, `03-workflow-02`, `04-workflow-03` e `05-testes-banco`. |
| `scripts/` | Cálculo dos indicadores e do resumo semanal (somente leitura), testes e validação histórica (`scripts/README.md`). |
| `crm-mock-teste/` | Cópia isolada do CRM mock do desafio (idêntica a `crm-mock/`), para testar sem mexer no original. |
| `../webhook/` | Cópia do remetente e do lote do marketing (idêntica a `webhook/` do desafio, sem o `envios.log`). |

## Workflows

| Arquivo | Para quê | Situação |
|---|---|---|
| `workflows/wf01-recebimento-cadastro-leads.json` | Recebe o webhook do formulário, valida o HMAC, classifica, registra no SQLite, responde 200 e cria o negócio no CRM só para lead comercial, sem duplicar. | **Aprovado** no teste T1.005 (execução 355): lead comercial registrado e negócio 20395 criado. |
| `workflows/wf02-conciliacao-marketing-crm.json` | Concilia os eventos pendentes com o CRM: localiza o negócio pelo e-mail e marca `sync_eventos` como `sincronizado`; cria o negócio se faltar. | **Aprovado** na execução 356: evento 005 `sincronizado` com `deal_id` 20395, CRM sem duplicação (395). |
| `scripts/resumo_semanal.py` | Funil, pedidos, ausentes no CRM, prazo de primeiro contato e sem retorno, em JSON e em texto simples. | Validado em 12/10/2026: 23 de 23 números conferem com a apuração histórica. |
| `workflows/wf03-resumo-semanal.json` | Toda segunda às 08:00 (Brasília) chama o cálculo, monta o resumo e envia por e-mail se houver destinatário e credencial. | **Importado e executado à mão** (execuções 357 e 359, e-mail aceito pelo SMTP). **Não ativado**; agendamento não observado. Falta a atualização do `negocios_crm` e conferir o fuso do workflow. |

## Como executar o ambiente

Pré-requisitos: Python 3 (comando `py`) e n8n (`npx n8n`).

1. **CRM mock** (porta 8001):
   ```powershell
   cd solucao\crm-mock-teste
   py crm-mock.py            # continua do estado salvo
   py crm-mock.py --reset    # volta aos 391 negócios iniciais
   ```
   Conferir: abrir `http://127.0.0.1:8001/estado`.
   O CRM salva o estado em `crm-mock-estado.json` nesta mesma pasta (ignorado pelo git).

2. **n8n**: iniciar com `MESA_CERTA_HMAC_SECRET`, `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` e
   `NODE_FUNCTION_ALLOW_BUILTIN=crypto`, configurar as credenciais conforme
   `configuracoes/README.md` e importar os dois JSON de `workflows/`. Os nós SQLite
   são do pacote comunitário `n8n-nodes-sqlite3` (tipo `n8n-nodes-sqlite3.sqliteNode`).

3. **Enviar o lote** com o remetente do desafio (pasta `webhook/` na raiz do repositório):
   ```powershell
   cd webhook
   py enviar-lote.py --url http://127.0.0.1:5678/webhook-test/mesa-certa/marketing --limite 1
   ```
   O remetente grava `webhook/envios.log` com cada tentativa (ignorado pelo git).

## Implementação anterior

Antes de 28/10/2026 a solução era em Python (receptor HTTP, worker de
sincronização e 22 testes). Ela foi arquivada fora do repositório; as regras que
precisam ir para o n8n estão em `workflows/README.md`. Motivo da troca em
`../log-de-decisoes.md`.
