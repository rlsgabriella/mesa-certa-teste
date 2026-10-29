---
name: auditoria-workflow-crm
description: Audita workflows de automação e integração com CRM (n8n e similares) em modo somente leitura. Use ao revisar, validar ou aprovar um workflow que recebe webhooks, grava em banco e cria ou atualiza negócios no CRM, ou ao pedir auditoria, revisão de idempotência, tratamento de erros, evidências de execução ou relatório de aprovação de um workflow.
license: MIT
compatibility: Kiro; Windows ou Linux com Python 3.10+ (comando py ou python3) para o script de inspeção.
metadata:
  projeto: mesa-certa
  idioma: pt-BR
---

# Auditoria de workflow de integração com CRM

Produz um relatório que diz **o que está comprovado, o que não está e o que fazer**. Nada aqui altera workflow, banco, CRM ou credencial.
Regras do projeto (segredos, preservação de dados, evidências): `.kiro/steering/mesa-certa-projeto.md`.

## Antes de começar

- Confirme o alvo: arquivo exportado (`solucao/workflows/*.json`) ou workflow na instância (leitura por MCP, somente leitura).
- **Não** dispare webhook, execute workflow nem crie negócio no CRM. Se a auditoria pedir uma execução, descreva o teste e peça autorização.
- Nunca copie valores de segredo ou token para o relatório; cite só o nome da variável ou da credencial.

## Etapas

1. **Inspeção.** Rode `py .kiro/skills/auditoria-workflow-crm/scripts/inspecionar_workflow.py <workflow.json>` (opcional `--json`). Leia o inventário: nós, gatilhos, credenciais por referência, `pinData`, nós soltos, saídas de erro sem destino, referências a nós que não existem. Compare com a instância quando houver MCP (versão, número de nós, `updatedAt`).
2. **Entradas.** Para cada gatilho confira: autenticação ou assinatura (HMAC sobre o corpo bruto, comparação em tempo constante, formato do cabeçalho), campos obrigatórios, normalização (e-mail em minúsculas e sem espaços, telefone só com dígitos), fusos (UTC x Brasília) e o que acontece com entrada inválida (código 4xx, sem reenvio).
3. **Saídas.** Para cada chamada ao CRM e escrita em banco confira método, campos enviados e mapeados, nomes de chave exatos (sem `=` sobrando), autenticação por credencial, resposta ao remetente e o **tempo** até ela (um limite de 5 s com reenvio exige responder antes de falar com o CRM).
4. **Idempotência.** Existe chave de evento (`event_id`) e proteção em três camadas? Consulta antes de criar; `INSERT` com `NOT EXISTS`, `ON CONFLICT` ou chave única; `UPDATE` com condição de estado. Verifique reenvio do mesmo evento, mesma pessoa com outro evento, e CRM que grava mesmo respondendo 500 (consultar antes de repetir o POST). Detalhes em `references/checklist.md`.
5. **Tratamento de erros.** 401/422/409/429/500, resposta 200 com erro no corpo, timeout, falha de banco, retry com espera, saída de erro conectada, registro da falha e estado intermediário que não fica preso (`pendente` x `falha`). Falha não pode virar sucesso silencioso.
6. **Evidências.** Para cada execução citada: ID, horário (Brasília e UTC), nós executados e os que **não** rodaram, e conferência **independente** do estado final no CRM e no banco (contagem antes e depois, registro criado, ausência de duplicata). Registre os caminhos **não** executados (suporte, reenvio, assinatura inválida, falhas do CRM, criação por conciliação). Print não é obrigatório se relatório, JSON e estado do CRM provam a execução.
7. **Segurança.** Segredos em credencial ou variável, nunca no JSON, em `pinData` ou em log. Hash ou derivado do segredo em `console.log` é risco. Acesso a `$env` e módulos liberados exigem justificativa.
8. **Relatório.** Preencha `references/modelo-relatorio.md`: veredito por caminho (aprovado, aprovado com ressalvas, não comprovado, reprovado), achados com severidade, evidências, limitações e próximos passos. Separe **sugestão** (da auditoria) de **decisão** (da autora). Não declare "aprovado" para o que não foi executado.

## Saída esperada

Um arquivo Markdown em `solucao/evidencias/` (ou no local indicado), com tabela de achados e tabela de caminhos testados e não testados. Se algo afetar entrega (segredo, dado pessoal, número divergente), diga no topo.

## Exemplo de uso

> `/auditoria-workflow-crm` Audite `solucao/workflows/wf01-recebimento-cadastro-leads.json` e diga quais caminhos estão comprovados pela execução 355.

O Kiro roda o script, lê os resultados, confere as evidências existentes e entrega o relatório sem executar nada.
