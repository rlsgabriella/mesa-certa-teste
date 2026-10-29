# Log de decisões: Mesa Certa

Horários em Brasília (UTC-3). As execuções do n8n vêm em UTC e estão convertidas. Esta versão resume o log original de
27 a 29/10/2026; a cópia integral anterior fica fora do pacote (`mesa-certa-teste-dev/log-de-decisoes.bkp-2026-10-29-pre-reescrita.md`).
Valores de segredos não aparecem aqui.

## Uso de IA e de ações manuais

- **Kiro** (assistente no editor): implementação de scripts e JSON, inspeção (workflows, banco e CRM por MCP somente leitura), testes, validações e documentação. Enviou os eventos de teste com `solucao/testar_webhook_hmac.py`, quando autorizado.
- **ChatGPT**: apoio ao planejamento, ao entendimento técnico e à revisão de alternativas. 
- **Ações manuais, sem IA:** edições no editor do n8n, reinícios do n8n com variáveis de ambiente, importação do WF02 v2, clique em "Execute workflow" do WF02, envio do e-mail de teste do WF03, publicação no GitHub e a retirada de três prints.
- Legenda das sugestões: **[aceita]**, **[rejeitada]**, **[revisada após teste]**.

## 27/10: diagnóstico e primeira arquitetura

- Decisão: analisar os dados antes de automatizar (banco, histórico de etapas, lote do webhook e documentação). Achados: divergência entre fontes, eventos repetidos, pedidos sem negócio e mistura de pedidos comerciais com suporte, fornecedor e teste. Contar negócios por data de atualização não é contar pedidos.
- Arquitetura inicial em Python + SQLite (receptor, worker de sincronização, 22 testes). **[revisada]** no dia seguinte.

## 28/10: n8n, segurança e primeira prova

- **Migração para n8n [aceita]:** fluxos visíveis e fáceis de explicar na avaliação. O Python antigo foi arquivado fora do repositório; sobrou só o necessário ao CRM mock e ao remetente do desafio.
- **00:33** primeiro teste ponta a ponta (`evt_500110`): criou o negócio 20392; a consulta seguinte o encontrou e não criou outro.
- **00:59 a 01:10** auditoria de dados e do repositório, só leitura, separando números confirmados de hipóteses.
- **Segurança [aceita]:** token do CRM em credencial Header Auth; segredo HMAC em variável `MESA_CERTA_HMAC_SECRET`; HMAC calculado sobre o corpo bruto (Raw Body).
- **Revisão de confiabilidade:** o WF01 não foi dado como pronto só porque o primeiro teste passou. Exigidos: HTTP 401 para assinatura inválida, resposta 200 antes das chamadas ao CRM e idempotência por `event_id`.
- **[rejeitada, adiada]** assistente conversacional para a gestora: prioridade para indicadores confiáveis e resumo semanal.

## 29/10: correções, testes e Workflow 02

- **01:38** correção manual no WF01: removido o `pinData` de teste e corrigida a chave `"=nome"` para `"nome"`. O Kiro confirmou por leitura.
- **01:42** T1 (execução 351): **reprovado**. O processo do n8n usava um segredo diferente do cliente; o Kiro recalculou o HMAC do corpo bruto e a assinatura do cliente estava correta. Não era defeito do workflow.
- **01:52** commit `2c3ef90` enviado ao GitHub (contém o segredo de teste do desafio; ver riscos).
- **10:44 e 10:57** n8n reiniciado manualmente: primeiro com `MESA_CERTA_HMAC_SECRET` e `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`; depois, com `NODE_FUNCTION_ALLOW_BUILTIN=crypto` acrescentada (ver a falha de `crypto` abaixo).
- **10:55, 11:00 e 11:14** execuções 352 a 354 falharam: `Module 'crypto' is disallowed` e duas vezes `WorkflowHasIssuesError`, sem executar nó algum. A causa exata não foi comprovada; a hipótese foi o tipo `CUSTOM.sqliteNode`.
- **11:18** troca manual dos 4 nós SQLite por `n8n-nodes-sqlite3.sqliteNode`. **[revisada após teste]** a padronização anterior para `CUSTOM.sqliteNode`, sugerida pelo Kiro em análise só estrutural.
- **11:33 execução 355: T1.005 aprovado** (UTC 14:33:02). Caminho executado: HMAC válido, classificação `comercial`, gravação no SQLite, resposta 200 e criação do negócio 20395. CRM de 394 para 395; `sync_eventos` ficou `pendente`. Foi **um** evento comercial. Logo depois (11:33:29) os 4 nós antigos e desconectados foram removidos manualmente; a versão exportada (18 nós) não foi executada.
- **WF02 [revisada após teste]:** o UPDATE de "Vincular Negócio Existente" passou de `ja_no_crm` para `sincronizado`, e o nó "Buscar Leads Pendentes" trocou `CUSTOM.sqliteNode` por `n8n-nodes-sqlite3.sqliteNode`. Cópia "corrigido v2" importada manualmente às 12:18.
- **13:17 execução 356: WF02 aprovado** (UTC 16:17:07), **só no caminho "negócio já existe"**: localizou o 20395 pelo e-mail e marcou o evento 005 como `sincronizado` com `deal_id` 20395. CRM continuou com 395. Os ramos de criação por POST e de erro não rodaram.
- **13:29** organização do repositório: exports finais do WF01 e do WF02 lidos da instância; segredo HMAC trocado por placeholder em `webhook/README.md` e removido deste log; backups e versões antigas movidos para `mesa-certa-teste-dev/`; `enunciado.md` copiado para a raiz.

## 29/10: análise histórica e Workflow 03

- **Análise dos dados (referência 12/10/2026 08:00):** funil 391 (106 Novo, 133 Contato, 43 Reunião marcada, 37 Reunião realizada, 72 Perdido). O 187 da planilha é contagem por data de atualização (142 criados mais 45 antigos). 175 pedidos distintos no lote, 136 comerciais, 12 sem correspondência no CRM, 68 sem contato com prazo de 4 h úteis vencido. Nenhuma culpa atribuída a SDR: diferença não significativa e autor do contato desconhecido. Negócios dos testes de 28 e 29/10 não entraram nos indicadores históricos.
- **14:00** WF03 preparado: `solucao/scripts/resumo_semanal.py` (somente leitura), 25 testes, validação histórica e `wf03-resumo-semanal.json`.
- **Validação [aprovada]:** 23 de 23 indicadores conferem com a apuração histórica, sem ajustes. Única diferença de definição: mediana de 2,08 h úteis contra 2,15 antes.
- **[rejeitada]** reativar o nó Execute Command (desativado no n8n 2.x) e **[rejeitada]** refazer os cálculos em Code nodes. **[aceita]** serviço HTTP local, só leitura, em `127.0.0.1:8002`.
- **[revisada após teste]** acrescentado o aviso "banco desatualizado", depois de ver que o banco de trabalho mostrava 391 negócios com o CRM em 395. A resposta a referência inválida passou de 500 para 400 sem novo teste manual.
- **14:53 e-mail manual do resumo, recebimento confirmado pelo Gmail** (print). O print não mostra ID de execução do n8n nem o corpo completo, então não prova que o envio saiu do agendamento nem do workflow importado.

## 29/10: evidências

- **15:06** `solucao/evidencias/` reorganizada em cinco subpastas (`01-auditoria`, `02-workflow-01`, `03-workflow-02`, `04-workflow-03`, `05-testes-banco`) com índice e limitações de cada prova; referências de caminho atualizadas.
- **Até 15:21** (horário deste registro) três prints do WF01 (`get.png`, `post.png`, `lead.png`) foram **retirados manualmente** por conterem informações que não serão publicadas. **Decisão: manter evidências textuais e estruturadas** (relatórios `.md` e `.json` das execuções 355 e 356, estado final do CRM, validação histórica do WF03). Os prints não eram obrigatórios; as imagens não foram recriadas e os links foram removidos.
- Resta `email-evidencia.png`, com dado pessoal (ver riscos). **Depois:** a autora retirou esse print manualmente (horário não registrado); referências ainda a atualizar.
- **Revisão do histórico git (Kiro, somente leitura):** um commit publicado (`2c3ef90`); o segredo HMAC de teste está nele em `log-de-decisoes.md` e `webhook/README.md`, e o token de teste do CRM em `crm-mock.py`; `.env` fora do histórico. Consulta anônima à página do repositório deu 404 e o Kiro leu isso como "privado"; **[revisada]** a autora informou que o repositório é **público**, então o segredo ficou exposto desde o push. **Sugestão do Kiro:** não reescrever o histórico. **[rejeitada]** pela autora, que pediu a limpeza.
- **Reescrita local do commit (Kiro, a pedido da autora):** backup em bundle fora do pacote; commit raiz refeito (`2c3ef90` para `6227691`) com o segredo HMAC trocado por placeholder em `log-de-decisoes.md` e `webhook/README.md` e sem os três prints do WF01. Conferido: nenhum resultado para o segredo no histórico do `main`, `git fsck` sem erros, `.env` fora do commit. O token do CRM segue em `crm-mock.py`. **Publicado após autorização expressa da autora:** `git push --force-with-lease` (`2c3ef90` para `6227691`). Conferido no remoto depois do `fetch`: sem o segredo no histórico e na árvore, sem imagens. O commit antigo pode seguir acessível pelo hash no GitHub e em cópias de terceiros.

## 29/10: pacote do assistente de IA (Kiro)

- **15:52** criado em `.kiro/` pelo Kiro, a pedido da autora, para cumprir o item do enunciado. Descrição, uso e validação em `.kiro/README.md`.
- **Instruções persistentes [aceita]:** `.kiro/steering/mesa-certa-projeto.md` com `inclusion: always` (segurança, preservação de dados, qualidade das evidências, validação de indicadores, limitações, IA x decisão humana). O Kiro as injetou como regra do workspace. **[rejeitada]** duplicar em `AGENTS.md`: o Kiro também o aceita, mas manter dois arquivos geraria divergência.
- **Skill [aceita]:** `.kiro/skills/auditoria-workflow-crm/` (`SKILL.md`, checklist, modelo de relatório e `scripts/inspecionar_workflow.py`, inspetor estático e somente leitura do JSON de workflows n8n). Na leitura dos três workflows: WF01 com 0 alertas e 2 avisos (criação do negócio sem retry; nó Code usa `$env` e `console.log`); WF02 com aviso de gatilho manual; WF03 sem alertas.
- **Hooks [aceita]:** `PostFileSave` e `PostFileCreate` executam `.kiro/scripts/verificar_publicacao.py`, que procura segredos e dados pessoais e só avisa (nunca bloqueia, altera ou apaga; não imprime valores). **[rejeitada]** hook `Stop` (um código de saída diferente de zero força outro turno do agente) e hook destrutivo ou que corrige sozinho; **[rejeitada]** `PreToolUse` por poder bloquear o trabalho.
- **Validação:** scripts compilam; `--autoteste` com 12 verificações aprovado; hook simulado com eventos sintéticos (arquivo com segredo: alerta sem exibir o valor; arquivo limpo: sem alerta; hashes inalterados); varredura `--git`: 43 arquivos, 0 alertas, 2 avisos (`mesa_certa.db` e `email-evidencia.png`).
- **Limitações:** o Kiro informou que os hooks passam a valer na próxima sessão; o disparo automático real **ainda não foi observado** (só simulado) e os gatilhos de arquivo valem para alterações do agente, não para edição manual. A skill ainda não foi acionada em uma conversa. A detecção é por padrão e por valor; imagens e bancos não são lidos. O comando `py` é do Windows. Pasta `.kiro/` ainda não versionada (decisão de commit é da autora).

## 29/10: teste do agendamento do WF03

- **Execuções vistas no n8n (Kiro, leitura):** 357 (14:53:13, sucesso, "Enviar e-mail" aceito pelo SMTP; coincide com o e-mail de teste das 14:53), 358 (14:56, cancelada), 359 (16:19:37, sucesso, e-mail aceito) e 360 (16:19:52, só o gatilho). Todas em modo `manual`. Isso substitui a limitação anterior ("importação não documentada"); o destinatário não é registrado aqui.
- **Teste de 16:20 (autora):** a autora ajustou o cron para `0 20 16 * * *` e publicou, mas **não houve execução agendada**. Às 16:27 o n8n mostrava o workflow com `active: false`, sem versão publicada, e o cron de volta em `0 8 * * 1`. O motivo da falha na publicação não aparece pela API; falta a mensagem exibida na tela.
- **Causa provável do horário [descoberta do Kiro]:** o export do repositório tem `settings.timezone = America/Sao_Paulo`, mas o workflow importado não tem. A execução 360 mostra o gatilho em `America/New_York` (UTC-4). Um cron para 16:20 dispararia às 17:20 em Brasília, e a segunda às 08:00 sairia às 09:00 em Brasília. A correção é manual: Settings do workflow, Timezone `America/Sao_Paulo`.
- **Próximo teste:** com o fuso corrigido, cron para poucos minutos à frente, publicar e acompanhar a lista de execuções; só uma execução de modo `trigger` comprova o agendamento. **[pendente]**

## Status final (29/10/2026, 15:21)

**Comprovado**
- WF01: um lead comercial com HMAC válido foi aceito e virou negócio no CRM (execução 355).
- WF02: execução 356 vinculou um negócio existente e atualizou `sync_eventos`, sem duplicar o CRM.
- WF03: cálculo reproduz a apuração histórica (23 de 23); 25 testes automatizados passam; e-mail de teste manual recebido.
- `mesa_certa.original.db` intacto; registros dos testes documentados em `solucao/evidencias/05-testes-banco/`.

**Limitações reais**
- WF01 sem execução de: suporte ou não comercial, reenvio do mesmo `event_id`, assinatura inválida (401), falhas 429/500 e lote completo. As execuções 353 e 354 não tiveram causa comprovada.
- WF02 sem execução do ramo de criação por POST, do tratamento de erro e de vários eventos.
- WF03: **agendamento automático (segunda 08:00) não comprovado.** Está importado e foi executado à mão (357 e 359); a cópia importada não tem fuso definido (ver "Teste do agendamento").
- **A cópia SQLite do CRM está desatualizada** (último registro em 11/10; o CRM mock já passou de 391 para 395 negócios). O resumo de 29/10 mostra 0 negócios na semana e só vale como teste de envio: **não deve ser lido como visão atual da operação**.
- A classificação de pedidos (comercial, suporte, fornecedor, teste, lixo) é regra por texto, não validada por pessoas.


**Pendências para a entrega**
- Revisão de segurança do histórico do GitHub: histórico reescrito e publicado (ver README, seção 7). Falta a troca do segredo HMAC por quem o forneceu, já que o repositório é público e o valor ficou exposto; decisão da autora.
- Comprovar o agendamento do WF03 e atualizar o `negocios_crm` antes de qualquer resumo real.
- Observar o primeiro disparo automático dos hooks e o uso da skill em uma conversa nova.
- Cenários sem execução listados em "Limitações reais".
