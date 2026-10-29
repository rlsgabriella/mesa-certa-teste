# Log de Decisões — Desafio Mesa Certa

Este documento registra as principais decisões técnicas e de negócio tomadas durante o desenvolvimento da solução Mesa Certa, incluindo o uso de assistentes de IA, as alternativas consideradas e os resultados obtidos.

## 27/10/2026 — Diagnóstico inicial

**Decisão:** começar pela análise dos dados antes de implementar automações.

Foram examinados o banco SQLite, o histórico de etapas do CRM, os eventos enviados pelo marketing e a documentação da API.

O diagnóstico identificou divergências entre as fontes, eventos duplicados, pedidos sem correspondência identificada no CRM e registros que exigiam classificação entre oportunidades comerciais e solicitações não comerciais.

A análise também mostrou que contar negócios pela data de atualização não equivale a contar pedidos de demonstração recebidos na semana.

**Uso da IA:** apoio na exploração dos dados, elaboração das consultas e identificação de possíveis causas das divergências.

**Resultado:** diagnóstico preliminar concluído. A conciliação definitiva e os números para a gestora ainda precisam ser validados.

## 27/10/2026 — Escolha inicial da arquitetura

**Decisão inicial:** desenvolver a integração utilizando Python e SQLite, com comunicação pela API REST do CRM.

A abordagem permitiria implementar validação de webhooks, tratamento de duplicidades e sincronização com o CRM.

Foram criados componentes de integração e executados testes automatizados, que passaram na versão inicial.

**Uso da IA:** apoio na estruturação do código e na elaboração dos testes.

**Resultado:** a abordagem foi tecnicamente explorada, mas posteriormente substituída como solução principal.

## 28/10/2026 — Migração de Python para n8n

**Decisão:** utilizar o n8n como ferramenta principal de automação.

**Justificativa:** facilitar a visualização dos processos, a manutenção dos fluxos e a explicação da solução durante a avaliação técnica.

A implementação anterior em Python foi arquivada fora do repositório. O Python foi mantido apenas onde necessário para executar as ferramentas fornecidas pelo desafio, como o CRM mock.

**Alternativa descartada:** manter uma integração própria em Python como solução principal, por exigir mais código e manutenção para o escopo proposto.

**Uso da IA:** apoio na comparação das alternativas, organização do repositório e preservação dos arquivos originais.

## 28/10/2026 — Preservação dos dados e evidências

**Decisão:** trabalhar com cópias dos dados e preservar evidências das alterações realizadas no CRM.

Os arquivos originais foram conferidos, a estrutura do repositório foi reorganizada e foram mantidos registros do negócio de teste criado durante a integração.

**Justificativa:** permitir a reprodução dos testes sem comprometer os dados originais.

**Resultado:** estrutura preparada para armazenar workflows, configurações e evidências.

## 28/10/2026 — Implementação do Workflow 01

**Decisão:** iniciar pela automação de recebimento e cadastro de leads do marketing.

O workflow foi estruturado para receber eventos por webhook, validar assinaturas HMAC, preparar os dados, consultar o CRM e registrar pedidos no SQLite.

Foram implementadas consultas por `event_id` para identificar eventos já registrados e evitar inserções repetidas na tabela de pedidos.

**Resultado dos testes:** um evento de teste foi registrado no SQLite e uma nova consulta identificou corretamente sua existência.

**Limitação:** a prevenção de duplicidade no CRM ainda não está garantida, pois a verificação no SQLite e a integração com o CRM precisam ser encadeadas corretamente.

## 28/10/2026 — Segurança das credenciais

**Decisão:** não armazenar tokens de autenticação ou o segredo HMAC diretamente nos nós exportados do n8n.

O token do CRM passou a ser utilizado por meio de credenciais Header Auth, compartilhadas entre os nós GET e POST.

A validação HMAC passou a utilizar a variável de ambiente `MESA_CERTA_HMAC_SECRET`.

**Uso da IA:** apoio na configuração e revisão das credenciais.

**Verificação:** o Kiro realizou auditorias do JSON exportado. A auditoria mais recente não encontrou tokens nem segredos expostos e confirmou a referência correta à variável HMAC.

**Resultado:** correção de exposição de credenciais concluída no arquivo auditado.

## 28/10/2026 — Revisão da confiabilidade da integração

**Decisão:** não considerar o Workflow 01 finalizado apenas porque os testes iniciais passaram.

A auditoria identificou duas correções essenciais:

- Retornar HTTP 401 quando a assinatura do webhook for inválida.
- Garantir que eventos duplicados não possam gerar novos negócios no CRM.

Também foram identificados tratamentos necessários para falhas e respostas inesperadas da API.

**Uso da IA:** o Kiro foi utilizado para inspecionar o workflow exportado e identificar riscos que não haviam sido cobertos pelos testes iniciais.

**Decisão aceita:** corrigir a sequência dos nós e os tratamentos de erro antes da validação final.

**Resultado:** problemas identificados e documentados; implementação pendente.

## 28/10/2026 — Planejamento das próximas automações

**Decisão:** priorizar os resultados solicitados pela gestora, sem criar workflows desnecessários.

A solução deverá contemplar o acompanhamento do funil comercial, a conciliação dos pedidos de demonstração, a identificação de atrasos no primeiro contato, os pedidos ausentes no CRM e o resumo semanal automático.

O Workflow 02 foi iniciado para consultas e indicadores no SQLite, mas ainda não foi concluído.

**Alternativa adiada:** implementar um assistente conversacional para responder perguntas da gestora. A prioridade será entregar primeiro indicadores confiáveis e um resumo semanal automatizado.

**Justificativa:** concentrar o esforço nas funcionalidades obrigatórias e manter a solução simples de operar.

## 29/10/2026 — Exportação e correção técnica dos Workflows 01 e 02

**Decisão:** corrigir defeitos nos JSONs exportados dos dois workflows antes de seguir para a documentação, com cópia de backup das versões anteriores em `solucao/workflows/backup/`.

**Verificação (via leitura dos JSONs e do banco, somente leitura):**
- Os dois workflows já estavam exportados em `solucao/workflows/`.
- Nenhum segredo/token/Bearer exposto nos JSONs (credenciais por referência).
- Banco: `pedidos_formulario` com coluna `classificacao` e 104 linhas, **todas `nao_classificado`**; `sync_eventos` com 3 eventos `sincronizado` (deal_id 20392–20394).

**Correções aplicadas (edição direta do JSON):**
- WF01: corrigido campo `"=nome"` → `"nome"` no POST ao CRM; removido `pinData` de teste. Confirmado que `Classificar Pedido` roda antes do INSERT e que a `classificacao` é persistida.
- WF02: removido `event_id` fixo de teste; `Vincular Negócio Existente` virou `UPDATE` (estado `ja_no_crm`); nós SQLite padronizados para `CUSTOM.sqliteNode`; completados os dois ramos do IF "Negócio criado após erro?" com dois nós novos (`sincronizado` / `falha`); corrigido e-mail do GET inicial.

**Sugestão da IA (Kiro) aceita:** padronizar o tipo de nó SQLite e persistir a classificação, pois sem isso o filtro `classificacao='comercial'` do WF02 nunca encontraria leads (todas as linhas estão `nao_classificado`).

**Limitação conhecida / não comprovado:** as correções foram validadas por **leitura estrutural**, não por execução. O terminal estava indisponível nesta sessão e o webhook de teste do n8n precisa ser armado manualmente. Logo, **não há evidência de execução** das versões corrigidas. Os 104 registros antigos seguem `nao_classificado` (decisão de não reclassificar automaticamente).

## 29/10/2026 — Verificação via MCP e preparo das versões corrigidas (sem aplicar)

**Contexto:** conectado o MCP `n8n-mcp` à instância local (após habilitar `WEBHOOK_SECURITY_MODE=moderate` e a Public API do n8n). Leitura dos dois workflows na instância confirmou o estado real.

**Fatos confirmados por leitura (MCP):**
- WF01 (`bZu7Ku16BbgSj504`, 18 nós): ordem correta e `classificacao` já persistida no INSERT. **Dois defeitos reais:** campo `"=nome"` no POST ao CRM e `pinData` de teste ativo em "Preparar Dados do Lead" (`teste-suporte-real-005`, mensagem de suporte), que faz toda execução ignorar o webhook real.
- WF02 (`tTDsv01lkDZqTnp1`, 10 nós): `Vincular Negócio Existente` ainda com `SELECT` e `event_id` fixo; faltam os dois nós do ramo de erro; GET inicial com espaço no e-mail.
- Credenciais por referência coincidem entre repo e instância (CRM `rmoFJ2XC21kBrCVT`, SQLite `A6Zo3HG9VmdtVFOr`).

**Correção de decisão anterior (tipos de nó SQLite):** na auditoria anterior eu havia padronizado tudo para `CUSTOM.sqliteNode`. A leitura da instância mostrou que **os dois tipos coexistem e já executaram** (`n8n-nodes-sqlite3.sqliteNode` nos nós de UPDATE do WF02; `CUSTOM.sqliteNode` nos demais). Além disso, os dois tipos usam **formatos diferentes de `queryReplacement`**: `CUSTOM` usa array (`={{ [a, b] }}`), enquanto `n8n-nodes-sqlite3` usa string separada por vírgula (`={{ a }},{{ b }}`), formato que já roda na instância. **Decisão revista:** preservar o tipo original de cada nó e o formato de parâmetro correspondente, em vez de padronizar. A versão do repo que havia padronizado foi substituída por uma preparada em `solucao/workflows/corrigidos/`.

**Preparado (não aplicado na instância):**
- `solucao/workflows/corrigidos/Mesa Certa _ 01 ...corrigido.json`: `"=nome"`→`"nome"`, `pinData` removido.
- `solucao/workflows/corrigidos/Mesa Certa_02-Conciliacao Marketing x CRM.corrigido.json`: `Vincular` vira UPDATE `ja_no_crm` (tipo `n8n-nodes-sqlite3`, parâmetro string vírgula), event_id dinâmico, GET corrigido, + 2 nós de erro (`sincronizado`/`falha`) com conexões do IF.
- Backups das versões exportadas em `solucao/workflows/backup/`.

**Uso da IA (Kiro):** leitura e comparação via MCP, preparo dos JSONs e validação estrutural.

**Limitação:** validação apenas estrutural (leitura). **Não executado** na instância; nada importado. Pendente de autorização para aplicar e testar.

## 29/10/2026 — Correção pontual aplicada ao Workflow 01 (instância n8n)

**Decisão:** aplicar manualmente no editor do n8n as duas correções pontuais do WF01 (`bZu7Ku16BbgSj504`), já que o MCP `n8n-mesa-certa` está em modo somente leitura (as ferramentas de escrita `n8n_update_partial_workflow`/`update_full` não foram expostas). Evitou-se substituir o workflow inteiro.

**Alterações (feitas pela usuária no editor, salvas):**
1. Removido o `pinData` de teste do nó "Preparar Dados do Lead" (era `teste-suporte-real-005`, mensagem de suporte). Agora `pinData: {}` — o workflow volta a processar os dados do webhook.
2. No nó "Criar Negócio no CRM", a chave do 1º body parameter passou de `"=nome"` para `"nome"` (modo Fixed).

**Verificação (Kiro, via MCP n8n_get_workflow mode=full):** confirmadas as duas: `pinData: {}` e `name: "nome"`. `versionCounter` 376, `updatedAt` 2026-10-29T04:38:30. Nenhum outro nó/conexão/credencial alterado.

**Backup:** estado anterior (com pin e `=nome`) salvo em `solucao/workflows/backup/Mesa Certa _ 01 - instancia-antes-correcao-pontual.bkp.json`.

**Uso da IA (Kiro):** diagnóstico, leitura e verificação via MCP; a edição foi manual.

**Limitação:** correção confirmada estruturalmente, **não validada por execução**. O teste de ponta a ponta (comercial cria / suporte não cria / idempotência) ainda não foi rodado.

## 29/10/2026 — T1 (lead comercial, HMAC válida): NÃO APROVADO

**Objetivo do T1:** comprovar de ponta a ponta que um lead comercial com assinatura válida é classificado como `comercial` e gera negócio no CRM.

**Disparo:** evento `evt_t1_comercial_001`, e-mail `carla.comercial.t1@exemplo.com.br`, mensagem "Quero uma demonstracao do sistema de voces", enviado ao endpoint de teste `/webhook-test/mesa-certa/marketing` (workflow não ativo). Baseline do CRM antes: total 394 / Novo 109 / Contato 133 / Reunião marcada 43 / Reunião realizada 37 / Perdido 72.

**Resultado:** execução n8n id 351 terminou `success`, mas o nó "Validar Assinatura HMAC" retornou `assinatura_valida: false` → fluxo seguiu para o ramo **HTTP 401** ("Rejeitar Assinatura Inválida"). Os nós Classificar / Pedido é comercial / Criar Negócio **não executaram**. **Nenhum negócio foi criado no CRM** (permanece 394 / Novo 109).

**Verificação da causa (prova):**
- O corpo bruto recebido pelo n8n (279 bytes, lido do binário da execução) é idêntico ao enviado pelo script — sem reserialização.
- Recalculado o HMAC-SHA256 desse corpo com o segredo `<SEGREDO_HMAC_DO_DESAFIO>`: o hash resultante é **igual** ao `X-Signature` enviado pelo script. Ou seja, a assinatura do cliente está correta para esse segredo.
- Conclusão: a divergência está no **segredo efetivo carregado pelo processo do n8n** (`$env.MESA_CERTA_HMAC_SECRET`), que não corresponde a `<SEGREDO_HMAC_DO_DESAFIO>`. Consistente com a divergência de fingerprints observada antes entre ambientes.

**Status:** T1 **NÃO APROVADO** (bloqueado por configuração do segredo no processo n8n). Não é defeito do workflow nem do script de teste.

**Pendência:** alinhar `MESA_CERTA_HMAC_SECRET` no processo do n8n ao valor do desafio e reexecutar o T1. Reinício do n8n e novos testes aguardam autorização.

**Uso da IA (Kiro):** leitura da execução via MCP, decodificação do corpo e recálculo do HMAC para localizar a causa.

## Estado atual e próximos passos

**Concluído ou validado parcialmente:**
- Diagnóstico inicial dos dados.
- Definição do n8n como ferramenta principal.
- Preservação dos arquivos e evidências.
- Estrutura inicial da integração Marketing → CRM.
- Teste de registro e identificação de evento repetido no SQLite.
- Auditoria de credenciais do JSON exportado.

**Implementado no JSON, falta comprovar por execução:**
- Resposta HTTP 401 para assinatura inválida (nó dedicado no WF01).
- Resposta HTTP 200 após persistir, antes das chamadas ao CRM.
- Classificação do pedido e bloqueio de não comerciais no caminho do CRM.
- Reconciliação do WF02 (GET antes de POST, re-GET após erro, atualização de estado).

**Pendente:**
- Executar e comprovar os workflows 01 e 02 corrigidos (teste de ponta a ponta: comercial cria / suporte não cria / reconciliação).
- Concluir a conciliação e validar os números apresentados à gestora.
- Finalizar os indicadores comerciais e a análise do SLA de atendimento.
- Implementar o resumo semanal automático.
- Validar o estado final do CRM e registrar evidências do lote completo.
- Concluir a documentação obrigatória e o pacote do assistente de IA.

**Critério para conclusão:** a solução deverá funcionar de forma reproduzível, sem exposição de credenciais, sem exigir mudanças na rotina do time comercial e com resultados comprovados pelos dados e pelo estado final do CRM.