# Como assumir o projeto

Resumo técnico para quem continuar. Estado em 29/10/2026. Provas e limitações: [`README.md`](README.md) e [`solucao/evidencias/README.md`](solucao/evidencias/README.md).

## Arquitetura

```
Formulário --POST--> [WF01 n8n :5678] --> SQLite (pedidos_formulario, sync_eventos) --> CRM mock :8001
                      HMAC, classifica,                                                   ^
                      responde 200                                [WF02 manual] localiza o negócio e marca 'sincronizado'
SQLite --leitura--> resumo_semanal.py (--servir :8002) <--GET-- [WF03 n8n, segunda 08:00] --> e-mail
```

- **WF01** (`solucao/workflows/wf01-…json`, id `bZu7Ku16BbgSj504`): webhook `/webhook/mesa-certa/marketing` (teste: `/webhook-test/…`), valida a assinatura sobre o corpo bruto, classifica, grava, responde 200 e cria o negócio só para pedido comercial.
- **WF02** (`wf02-…json`, id `fcMKsKzpcdAMKnr0`): gatilho **manual**; busca eventos `pendente` e comerciais, consulta o CRM por e-mail e vincula ou cria o negócio.
- **WF03** (`wf03-…json`, id `wrGCERjaPYAeDcuH`): Schedule `0 8 * * 1`, chama o serviço de indicadores e envia o e-mail se houver destinatário. O JSON traz o fuso `America/Sao_Paulo`; **confira em Settings do workflow**, porque a primeira cópia importada veio sem fuso e usou `America/New_York`. No n8n ele está configurado para segunda 08:00 e **inativo**: ative-o para o envio semanal começar.
- **Cálculo** (`solucao/scripts/resumo_semanal.py`): só lê o SQLite; gera JSON e texto; a data de referência é parâmetro.

## Configuração (sem segredos)

- Windows, Python 3.10+ (`py`, só biblioteca padrão), n8n 2.x (`npx n8n`) com o pacote comunitário `n8n-nodes-sqlite3`. Use `127.0.0.1`, não `localhost` (no Windows o IPv6 atrasa cada chamada).
- Variáveis no processo do n8n: `MESA_CERTA_HMAC_SECRET` (valor do desafio), `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`, `NODE_FUNCTION_ALLOW_BUILTIN=crypto`; para o WF03, `RESUMO_SEMANAL_DESTINATARIO` e `RESUMO_SEMANAL_REMETENTE`. Modelo em `solucao/configuracoes/.env.example`; o `.env` real é ignorado pelo git.
- Credenciais no n8n: Header Auth do CRM (`Authorization: Bearer <token de teste do desafio>`), SQLite apontando para `mesa_certa.db` e SMTP para o WF03. Os ids de credencial nos JSON são da instância original: reassocie ao importar.
- Segredos nunca vão para o repositório (o token de teste do CRM é constante do `crm-mock.py`, arquivo do desafio). Antes de exportar um workflow, procure os valores reais no JSON.

## Execução

1. CRM: `cd solucao\crm-mock-teste; py crm-mock.py` (`--reset` volta aos 391 negócios).
2. n8n com as variáveis acima; importe os três JSON como workflows **novos** e revise antes de substituir algum em uso.
3. WF01 em "Listen for test event" e `py solucao\testar_webhook_hmac.py --event-id evt_novo_001 --email novo@exemplo.test --mensagem "Quero uma demonstracao"` (segredo na sessão). Depois, WF02: "Execute workflow".
4. WF03: suba o serviço (`py solucao\scripts\resumo_semanal.py --servir --porta 8002 --db mesa_certa.db`), crie a credencial SMTP e só então ative. Resumo sem n8n: `py solucao\scripts\resumo_semanal.py --saida texto`.

## Regras que o código implementa

- **Assinatura:** HMAC-SHA256 do corpo bruto (Raw Body), comparado em tempo constante; inválida responde 401. O lote tem 3 entregas inválidas, que não entram em contagem nenhuma.
- **Duplicidade:** mesmo `event_id` processa uma vez. Eventos diferentes da mesma pessoa: consultar `GET /deals?email=` antes de criar. E-mail e telefone apontando para negócios diferentes vão para revisão.
- **Normalização:** e-mail com `trim` e minúsculas; telefone só dígitos, sem o `55`.
- **CRM mock:** 409 é sucesso (usar o `deal_id`); 429 espera o `Retry-After`; 500 e `200 {"status":"erro"}` repetem com espera crescente. No POST, metade dos 500 grava o negócio, então consulte o CRM antes de repetir. Há atrasos de até 8 s.
- **Classificação:** comercial, suporte, fornecedor, teste ou spam, por texto. O marcador `test` não pode pegar "testar".
- **Indicadores:** pedidos contados pela data de **criação** (o 187 da planilha é a data de **atualização**). Prazo de 4 horas úteis, seg a sex, 8h às 18h (Brasília), sem descontar feriados. O SDR é o responsável do negócio, não quem ligou.

Testes e validação histórica: `solucao/scripts/README.md`. Execuções 355, 356 e 361: `solucao/evidencias/`.

## Assistente de IA (Kiro)

Pasta `.kiro/` ([`.kiro/README.md`](.kiro/README.md)): instruções fixas, skill `/auditoria-workflow-crm` e hooks que avisam sobre segredos ao salvar ou criar arquivos. Checagem manual antes de publicar: `py .kiro/scripts/verificar_publicacao.py --git`.

## Manutenção

- A classificação existe em dois lugares com níveis diferentes: o Code node "Classificar Pedido" do WF01 (simples) e `classificar_pedido` em `resumo_semanal.py` (mais fina). Alinhe ao mexer em uma.
- Antes de qualquer resumo real, atualize `negocios_crm` a partir do CRM. Nada faz isso hoje; o script avisa "banco desatualizado" quando o último registro tem mais de 3 dias.
- `mesa_certa.original.db` não se altera. Para zerar os testes, copie-o por cima de `mesa_certa.db` e rode o CRM com `--reset`.

## Limitações

- Um caminho comprovado por workflow: lead comercial (WF01) e vínculo de negócio existente (WF02). Sem execução: suporte, reenvio, assinatura inválida (401), falhas 429/500, criação por conciliação e lote completo.
- WF03: o agendamento foi provado na execução 361, com um horário de teste (mesmo gatilho e fuso). O workflow está inativo até alguém ativá-lo. O WF02 não é agendado.
- O banco não registra quem fez o contato; o prazo por SDR não prova atraso individual.
- O WF01 grava o hash do segredo no log do n8n (`console.log`); remova antes de uso fora do teste.
- O repositório é público e o segredo HMAC de teste esteve no commit `2c3ef90`, que pode seguir acessível pelo hash: peça a troca do valor.
