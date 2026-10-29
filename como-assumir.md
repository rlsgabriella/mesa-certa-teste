# Como assumir o projeto

Resumo técnico para quem continuar. Estado em 29/10/2026. O que está comprovado e o que não está: [`README.md`](README.md) e [`solucao/evidencias/README.md`](solucao/evidencias/README.md).

## Arquitetura

```
Formulário --POST--> [WF01 n8n :5678] --> SQLite (pedidos_formulario, sync_eventos) --> CRM mock :8001
                      HMAC, classifica,                                                   ^
                      responde 200                                [WF02 manual] localiza o negócio e marca 'sincronizado'
SQLite --leitura--> resumo_semanal.py (--servir :8002) <--GET-- [WF03 n8n, segunda 08:00] --> e-mail
```

- **WF01** (`solucao/workflows/wf01-…json`): webhook `/webhook/mesa-certa/marketing` (teste: `/webhook-test/…`), valida a assinatura sobre o corpo bruto, classifica, grava, responde 200 e cria o negócio só para pedido comercial.
- **WF02** (`wf02-…json`): gatilho **manual**; busca eventos `pendente` e comerciais, consulta o CRM por e-mail e vincula ou cria o negócio.
- **WF03** (`wf03-…json`): Schedule `0 8 * * 1`; o JSON traz `timezone` America/Sao_Paulo, mas **confira em Settings do workflow no n8n**, pois a cópia importada veio sem fuso e usou America/New_York. Chama o serviço de indicadores e envia o e-mail se houver destinatário.
- **Cálculo** (`solucao/scripts/resumo_semanal.py`): só lê o SQLite; gera JSON e texto; a data de referência é parâmetro.

## Dependências

Windows, Python 3.10+ (comando `py`, só biblioteca padrão), n8n 2.x (`npx n8n`) com o pacote comunitário `n8n-nodes-sqlite3` 1.1.1, CRM mock e remetente do desafio.

## Configuração (sem segredos)

- Variáveis no processo do n8n: `MESA_CERTA_HMAC_SECRET` (valor do desafio), `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`, `NODE_FUNCTION_ALLOW_BUILTIN=crypto`; para o WF03, `RESUMO_SEMANAL_DESTINATARIO` e `RESUMO_SEMANAL_REMETENTE`. Modelo em `solucao/configuracoes/.env.example`; o `.env` real é ignorado pelo git e não vai na entrega.
- Credenciais no n8n: Header Auth do CRM (`Authorization: Bearer <token de teste do desafio>`) e SQLite apontando para `mesa_certa.db`; SMTP para o WF03. Os ids das credenciais nos JSON são da instância original: reatribua ao importar.

## Execução

1. CRM: `cd solucao\crm-mock-teste; py crm-mock.py` (`--reset` volta aos 391 negócios).
2. n8n com as variáveis acima; importar os três JSON como workflows novos.
3. Teste do WF01: colocar o workflow em "Listen for test event" e rodar `py solucao\testar_webhook_hmac.py --event-id evt_novo_001 --email novo@exemplo.test --mensagem "Quero uma demonstracao"` (segredo na sessão).
4. WF02: "Execute workflow" depois do WF01.
5. WF03: `py solucao\scripts\resumo_semanal.py --servir --porta 8002 --db mesa_certa.db`; criar a credencial SMTP e o nó de e-mail; só então ativar.
6. Resumo na hora, sem n8n: `py solucao\scripts\resumo_semanal.py --saida texto` (use `--ref "2026-10-12 08:00"` para reproduzir uma data).

## Validação

- `py -m unittest solucao/scripts/test_resumo_semanal.py -v`: 25 testes.
- `py solucao\scripts\validar_resumo_historico.py`: reproduz 12/10/2026 08:00 sobre uma cópia de `mesa_certa.original.db` e do lote; 23 de 23 indicadores conferem ([relatório](solucao/evidencias/04-workflow-03/validacao-resumo-semanal-2026-10-12.md)).
- Execuções n8n 355 (WF01) e 356 (WF02), com SQLite e CRM conferidos, em `solucao/evidencias/`.

## Assistente de IA (Kiro)

Pasta `.kiro/`, descrita em [`.kiro/README.md`](.kiro/README.md): instruções fixas do projeto (`steering/`), skill `/auditoria-workflow-crm` para auditar workflows e hooks que avisam sobre segredos ao salvar ou criar arquivos. Checagem manual antes de publicar: `py .kiro/scripts/verificar_publicacao.py --git`.

## Manutenção

- A regra de classificação de pedidos existe em dois lugares com níveis diferentes: o Code node "Classificar Pedido" do WF01 (simples) e `classificar_pedido` em `resumo_semanal.py` (mais fina). Podem divergir; alinhe ao mexer em uma.
- Antes de qualquer resumo real, atualize `negocios_crm` a partir do CRM. Nada faz isso hoje; o script avisa "banco desatualizado" quando o último registro tem mais de 3 dias.
- `mesa_certa.original.db` não se altera; para zerar os testes, copie-o por cima de `mesa_certa.db` e rode o CRM com `--reset`.
- Backups e versões antigas dos workflows ficam fora do pacote (`mesa-certa-teste-dev/`).

## Limitações

- Comprovado um caminho por workflow: lead comercial (WF01) e vínculo de negócio existente (WF02). Sem execução: suporte, reenvio, assinatura inválida (401), falhas 429/500, criação por conciliação e lote completo.
- **Agendamento do WF03 não comprovado**; um e-mail de teste foi enviado manualmente. O WF02 não é agendado.
- O banco não registra quem fez o contato; o prazo por SDR é por responsável e não prova atraso individual.
- O WF01 grava o hash do segredo no log do n8n (`console.log`); remova antes de uso fora do teste.
- O histórico git (commit `2c3ef90`) contém o segredo e o token de teste do desafio; revisão de segurança pendente.
