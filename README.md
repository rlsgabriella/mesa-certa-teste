# Teste técnico Mesa Certa

Enunciado: [`enunciado.md`](enunciado.md) (cópia do original). Estado em 29/10/2026.

> **Status: a entrega ainda não está concluída.** A documentação obrigatória e o pacote do assistente Kiro (`.kiro/`) estão prontos, mas falta a revisão de
> segurança do GitHub (o histórico contém o segredo e o token de teste do desafio). Ver a seção 6.

## 1. O que a solução faz

Resolve, para a gestora comercial, o recebimento dos pedidos do formulário e os números que ela pediu, com n8n, SQLite e Python (Python só para o CRM mock, o remetente do desafio e o cálculo dos indicadores).

```
Formulário --POST--> WF01 --> SQLite (pedidos_formulario, sync_eventos) --> CRM mock (:8001)
                                                                             ^
                          WF02 (gatilho manual) localiza o negócio e marca o pedido 'sincronizado'
SQLite --leitura--> resumo_semanal.py --JSON/texto--> WF03 (segunda 08:00) --> e-mail
```

| Workflow | Função | Arquivo |
|---|---|---|
| **01** Recebimento de leads | Valida a assinatura, classifica, grava, responde 200 e cria o negócio no CRM só para pedido comercial. | [`wf01-recebimento-cadastro-leads.json`](solucao/workflows/wf01-recebimento-cadastro-leads.json) |
| **02** Conciliação | Para pedidos pendentes, localiza o negócio pelo e-mail e marca `sincronizado`; cria o negócio se faltar. | [`wf02-conciliacao-marketing-crm.json`](solucao/workflows/wf02-conciliacao-marketing-crm.json) |
| **03** Resumo semanal | Chama o cálculo (serviço local somente leitura) e envia o resumo por e-mail se houver destinatário. | [`wf03-resumo-semanal.json`](solucao/workflows/wf03-resumo-semanal.json) |

Cálculo dos indicadores: [`solucao/scripts/resumo_semanal.py`](solucao/scripts/resumo_semanal.py). Detalhes técnicos: [`como-assumir.md`](como-assumir.md).

## 2. Resultados comprovados

| Item | Resultado | Evidência |
|---|---|---|
| WF01, execução **355** (29/10) | Um lead comercial com assinatura válida: HTTP 200, classe `comercial`, pedido 105 no SQLite, negócio **20395** criado. CRM de 394 para 395. | [relato](solucao/evidencias/02-workflow-01/t1-005-aprovado.md), [JSON](solucao/evidencias/02-workflow-01/t1-005-resultado.json) |
| WF02, execução **356** (29/10) | Localizou o negócio 20395 já existente e marcou o pedido 005 como `sincronizado`, sem duplicar. CRM continua com 395. | [relato](solucao/evidencias/03-workflow-02/wf02-execucao-356.md), [JSON](solucao/evidencias/03-workflow-02/wf02-execucao-356.json) |
| WF03, cálculo | Referência 12/10/2026 08:00: **23 indicadores históricos** conferem com a apuração (funil 391, 187 atualizados, 142 criados, 136 pedidos comerciais, 12 sem correspondência, 68 sem retorno vencido). | [validação](solucao/evidencias/04-workflow-03/validacao-resumo-semanal-2026-10-12.md) |
| WF03, testes | **25 testes automatizados** aprovados (`py -m unittest solucao/scripts/test_resumo_semanal.py`). | [`test_resumo_semanal.py`](solucao/scripts/test_resumo_semanal.py) |
| WF03, e-mail | Execuções **357** (14:53) e **359** (16:19), ambas manuais e com sucesso: o nó "Enviar e-mail" foi aceito pelo SMTP. Recebimento das 14:53 confirmado pela autora no Gmail; o print foi retirado (dado pessoal). | Nota em [`solucao/evidencias/README.md`](solucao/evidencias/README.md) |

Os números da gestora (funil, 187, pedidos, prazo, ausentes) estão em [`respostas.md`](respostas.md). Índice completo das provas e limitações: [`solucao/evidencias/README.md`](solucao/evidencias/README.md).

## 3. Reprodução

Requisitos: Windows, Python 3.10+ (`py`), n8n 2.x com o pacote `n8n-nodes-sqlite3`. Modelo de variáveis: [`solucao/configuracoes/.env.example`](solucao/configuracoes/.env.example); nenhum segredo vai no repositório.

1. CRM mock: `cd solucao\crm-mock-teste; py crm-mock.py`.
2. n8n com `MESA_CERTA_HMAC_SECRET`, `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` e `NODE_FUNCTION_ALLOW_BUILTIN=crypto`; criar as credenciais (CRM e SQLite) e importar os três JSON de `solucao/workflows/`.
3. Enviar um pedido assinado: `py solucao\testar_webhook_hmac.py --event-id evt_novo_001 --email novo@exemplo.test --mensagem "Quero uma demonstracao"` com o workflow em "Listen for test event".
4. Resumo na hora: `py solucao\scripts\resumo_semanal.py --saida texto`. Reproduzir 12/10: `py solucao\scripts\validar_resumo_historico.py` (precisa do segredo do desafio na sessão).

## 4. Estrutura

```
README.md · problemas.md · respostas.md · suposicoes.md · como-assumir.md · guia-para-ela.md · quando-usar-o-que.md · log-de-decisoes.md
mesa_certa.original.db (intacto) · mesa_certa.db (trabalho, com registros de teste) · enunciado.md
solucao/  workflows/ (3 exports + README) · scripts/ · configuracoes/ · crm-mock-teste/ · evidencias/ (índice + 5 subpastas) · testar_webhook_hmac.py
webhook/  remetente e lote do marketing (segredo trocado por placeholder)
.kiro/    pacote do assistente: steering/ · skills/auditoria-workflow-crm/ · hooks/ · scripts/ · README.md
```

Fora do pacote: `../mesa-certa-teste-dev/` (backups e versões intermediárias; não enviar).

## 5. Limitações reais

- Cada workflow tem **um caminho** comprovado. Sem execução: suporte, reenvio do mesmo pedido, assinatura inválida (401), falhas 429/500 do CRM, criação de negócio pelo WF02, lote completo. O WF01 exportado (18 nós) não foi executado; a 355 rodou antes da remoção de 4 nós soltos.
- **Agendamento automático do WF03 não comprovado.** O workflow está importado (`wrGCERjaPYAeDcuH`) e rodou à mão nas execuções 357 e 359, mas está inativo e a cópia importada **não tem o fuso `America/Sao_Paulo`** (o n8n usou `America/New_York`). A tentativa de teste às 16:20 de 29/10 não gerou execução agendada. O WF02 tem gatilho manual.
- **A cópia SQLite do CRM está desatualizada** (último registro em 11/10). Relatórios operacionais atuais exigem atualizá-la; o e-mail de teste de 29/10 saiu com 0 negócios na semana e o aviso correspondente.
- A classificação de pedidos é uma regra por texto, sem revisão humana. Não há dado sobre quem fez cada contato, então o prazo por SDR não prova atraso individual.

## 6. Requisitos do enunciado

| Item | Situação |
|---|---|
| `problemas.md`, `respostas.md`, `suposicoes.md`, `como-assumir.md`, `guia-para-ela.md`, `quando-usar-o-que.md`, `log-de-decisoes.md` | Preenchidos. |
| `solucao/` com evidência no estado final do CRM | Presente para os caminhos testados (355 e 356). |
| Pacote do assistente de IA: instruções fixas | Criado: [`.kiro/steering/mesa-certa-projeto.md`](.kiro/steering/mesa-certa-projeto.md) (carregado em toda sessão). |
| Pacote do assistente de IA: procedimento reutilizável (skill) | Criado: [`.kiro/skills/auditoria-workflow-crm/SKILL.md`](.kiro/skills/auditoria-workflow-crm/SKILL.md); validado pelo script, ainda não acionado em conversa. |
| Pacote do assistente de IA: checagem automática (hook) | Criado: [`.kiro/hooks/`](.kiro/hooks/) (`PostFileSave` e `PostFileCreate`, só avisam); validado por simulação, disparo automático ainda não observado. Detalhes em [`.kiro/README.md`](.kiro/README.md). |
| Revisão de segurança do GitHub (histórico com segredo e token de teste, commit `2c3ef90`) | **Histórico limpo e publicado** (seção 7). **Pendente:** trocar o segredo HMAC, pois o repositório é público e o valor ficou exposto. |
| `email-evidencia.png` (e-mail e foto de perfil reais) | Retirado do pacote pela autora. Falta confirmar que não consta no histórico do GitHub. |
| Provar o agendamento do WF03 e atualizar a cópia do CRM | **Pendente** (não exigido para os documentos, necessário para uso operacional). |

## 7. Segurança

`.env` é ignorado pelo git e não deve ir na entrega. O WF01 grava o hash do segredo no log do n8n.

**Histórico git (levantamento de 29/10, somente leitura, valores não exibidos):**
- O repositório tem **um** commit, `2c3ef90`, já publicado em `origin/main` (`rlsgabriella/mesa-certa-teste`).
- Nesse commit, o **segredo HMAC de teste** aparece em `log-de-decisoes.md` e `webhook/README.md`. Nos arquivos atuais ele foi removido ou trocado por placeholder.
- O **token de teste do CRM** aparece em `solucao/crm-mock-teste/crm-mock.py`, arquivo do desafio, e continua no arquivo atual. Sem esse valor o CRM mock não autentica.
- O `.env` nunca entrou no histórico.
- **O repositório é público** (confirmado pela autora em 29/10). Uma consulta anônima feita pelo Kiro retornou 404, o que não indicava repositório privado; essa leitura estava errada.
- Os dois valores vieram do material do desafio e servem ao CRM mock local. Que não valem em outro sistema é uma suposição a confirmar pela autora.
- **Reescrita local (29/10, a pedido da autora):** o commit raiz foi refeito como `6227691`, com mesmo autor, data e mensagem. Nele, o segredo HMAC virou o placeholder `<SEGREDO_HMAC_DO_DESAFIO>` e os três prints do WF01 (`get.png`, `lead.png`, `post.png`) saíram. O token do CRM continua em `crm-mock.py`, arquivo do desafio, e nenhuma imagem consta no commit novo.
- **Publicado (29/10, push forçado autorizado pela autora):** `origin/main` agora está em `6227691`. Conferido depois do `fetch`: o segredo não aparece no histórico nem na árvore do remoto, e não há imagens no commit.
- **Exposição residual:** o repositório é público e o commit `2c3ef90` esteve online até o push. O GitHub pode manter esse hash acessível por um tempo, e cópias ou indexações de terceiros não dá para verificar daqui. O valor deve ser tratado como exposto; a correção completa é a troca do segredo por quem o forneceu. Backup do estado anterior fora do pacote: `mesa-certa-teste-dev/backup-antes-reescrita-2c3ef90.bundle`.
