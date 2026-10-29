# Solução — automações em n8n

A solução roda em n8n. Cada automação é um workflow exportado em JSON na pasta
`workflows/`. O Python fica só para subir o CRM mock fornecido pelo desafio.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `workflows/` | JSON dos workflows testados e as regras de negócio que cada um implementa (`workflows/README.md`). |
| `configuracoes/` | Endereços, como configurar credenciais no n8n e `.env.example` sem valores. |
| `evidencias/` | Prints e estado do CRM que provam o resultado, mais a auditoria dos dados. |
| `crm-mock-teste/` | Cópia isolada do CRM mock do desafio (idêntica a `crm-mock/`), para testar sem mexer no original. |
| `../webhook/` | Cópia do remetente e do lote do marketing (idêntica a `webhook/` do desafio, sem o `envios.log`). |

## Workflows

| Arquivo | Para quê | Situação |
|---|---|---|
| `01-integracao-marketing-crm.json` | Recebe o webhook do formulário, valida a assinatura e cria o negócio no CRM sem duplicar. | Em construção; testado com 1 evento. |
| `02-conciliacao-pedidos.json` | Compara os pedidos do marketing com o CRM e lista os que não chegaram. | Não iniciado. |
| `03-indicadores-sla.json` | Negócios por etapa e prazo de primeiro contato por SDR. | Não iniciado. |
| `04-resumo-semanal.json` | Resumo automático toda segunda de manhã para a gestora. | Não iniciado. |

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

2. **n8n**: configurar as credenciais conforme `configuracoes/README.md` e importar
   os workflows de `workflows/`.

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
