# Como assumir o projeto

Resumo técnico para quem continuar. Estado em 29/10/2026. Provas e limitações: [`README.md`](README.md) e [`solucao/evidencias/README.md`](solucao/evidencias/README.md).

## Como funciona em operação

Os três workflows do n8n ficam **ativos** e reagem a gatilhos, sem ninguém abrir nada:

```
Formulário --POST assinado--> [WF01 webhook] --> SQLite --> CRM mock :8001
                                                   |            ^
                              [WF02 conciliação] --+------------+   (hoje: gatilho manual)
SQLite --> resumo_semanal.py (:8002) <--GET-- [WF03, segunda 08:00] --> e-mail
```

- **WF01** (`bZu7Ku16BbgSj504`): cada pedido do formulário dispara o webhook `/webhook/mesa-certa/marketing`. Valida a assinatura, classifica, grava, responde 200 e cria o negócio só para pedido comercial.
- **WF02** (`fcMKsKzpcdAMKnr0`): concilia o que ficou pendente (localiza o negócio pelo e-mail e marca `sincronizado`). O gatilho é **manual**; em operação, o próximo passo é agendá-lo.
- **WF03** (`wrGCERjaPYAeDcuH`): Schedule de segunda 08:00 (`America/Sao_Paulo`). Chama o cálculo e envia o resumo por e-mail.
- **Cálculo** (`solucao/scripts/resumo_semanal.py`): só lê o SQLite; a data de referência é parâmetro.

Nesta entrega o WF03 foi deixado **desativado** no n8n depois do teste de agendamento (execução 361); em uso, ative-o. Para tudo isso funcionar, o n8n, o CRM e o serviço na porta 8002 precisam estar ligados.

## Configuração (sem segredos)

- Windows, Python 3.10+ (`py`), n8n 2.x com o pacote `n8n-nodes-sqlite3`. Use `127.0.0.1`, não `localhost`.
- Variáveis no processo do n8n: `MESA_CERTA_HMAC_SECRET`, `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`, `NODE_FUNCTION_ALLOW_BUILTIN=crypto`, e para o WF03 `RESUMO_SEMANAL_DESTINATARIO` e `RESUMO_SEMANAL_REMETENTE`. Modelo em `solucao/configuracoes/.env.example`; o `.env` é ignorado pelo git.
- Credenciais no n8n: Header Auth do CRM, SQLite apontando para `mesa_certa.db` e SMTP. Os ids nos JSON são da instância original: reassocie ao importar.
- Confira em Settings do WF03 o fuso `America/Sao_Paulo` (a primeira cópia importada veio sem ele).
- Segredo nunca vai para o repositório; antes de exportar um workflow, procure valores reais no JSON.

## Execução

1. CRM: `cd solucao\crm-mock-teste; py crm-mock.py` (`--reset` volta aos 391 negócios).
2. n8n com as variáveis acima; importe os três JSON de `solucao/workflows/` como workflows novos e ative-os.
3. Serviço do WF03: `py solucao\scripts\resumo_semanal.py --servir --porta 8002 --db mesa_certa.db`.
4. Teste do WF01: `py solucao\testar_webhook_hmac.py --event-id evt_novo_001 --email novo@exemplo.test --mensagem "Quero uma demonstracao"` (segredo na sessão). Resumo sem n8n: `py solucao\scripts\resumo_semanal.py --saida texto`.

## Regras que o código implementa

- **Assinatura:** HMAC-SHA256 do corpo bruto; inválida responde 401 e não entra em contagem.
- **Duplicidade:** mesmo `event_id` processa uma vez; antes de criar negócio, consulta `GET /deals?email=`. E-mail e telefone de negócios diferentes vão para revisão.
- **CRM mock:** 409 é sucesso; 429 espera o `Retry-After`; 500 repete com espera, mas no POST consulte antes (metade dos 500 grava o negócio).
- **Classificação:** comercial, suporte, fornecedor, teste ou spam, por texto.
- **Indicadores:** pedidos contados pela data de **criação** (o 187 da planilha é data de **atualização**); prazo de 4 horas úteis (seg a sex, 8h às 18h, Brasília), sem feriados.

## Manutenção e limitações

- A classificação existe no WF01 (simples) e em `resumo_semanal.py` (mais fina); alinhe ao mexer em uma.
- `negocios_crm` é uma cópia de 11/10 e nada a atualiza: atualize antes de qualquer resumo real (o script avisa "banco desatualizado").
- `mesa_certa.original.db` não se altera. Para zerar os testes, copie-o sobre `mesa_certa.db` e rode o CRM com `--reset`.
- Um caminho comprovado por workflow (WF01: lead comercial; WF02: vínculo de negócio existente). Sem execução: suporte, reenvio, assinatura inválida, falhas 429/500, criação por conciliação e lote completo.
- O banco não diz quem fez o contato; o prazo por SDR não prova atraso individual. O WF01 grava o hash do segredo no log (`console.log`); remova fora do teste.
- Assistente de IA: pasta [`.kiro/`](.kiro/README.md). Checagem antes de publicar: `py .kiro/scripts/verificar_publicacao.py --git`.
