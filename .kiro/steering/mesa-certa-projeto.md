---
inclusion: always
---

# Mesa Certa: instruções fixas do projeto

Projeto do teste técnico "Mesa Certa" (n8n + SQLite + Python). Idioma: português do Brasil, linguagem profissional e direta.
Ambiente: Windows, PowerShell, comando `py`. Horários sempre em Brasília (UTC-3); o formulário e o lote do webhook vêm em UTC.
Estado e provas: `README.md`, `solucao/evidencias/README.md`. Decisões: `log-de-decisoes.md`.

## 1. Segurança

- Nunca escrever, imprimir, registrar ou copiar valores de segredo, token, senha ou chave. Citar só o nome da variável (`MESA_CERTA_HMAC_SECRET`).
- Segredos ficam em variável de ambiente ou em credencial do n8n. O `.env` é ignorado pelo git e nunca entra em entrega, relatório, log ou print.
- Ao conferir um segredo, ler o valor em memória e comparar; nunca exibir o resultado da leitura.
- Antes de salvar ou publicar arquivos novos, verificar segredos e dados pessoais (`py .kiro/scripts/verificar_publicacao.py --git`).
- Dados pessoais só quando necessários à prova. Prints e e-mails reais não entram no pacote público sem a decisão da autora.

## 2. Preservação de dados e ações de risco

- `mesa_certa.original.db` é imutável. Conferir o SHA-256 antes e depois de qualquer análise. Análises rodam em modo somente leitura (`mode=ro`) ou sobre cópia.
- Não alterar `mesa_certa.db`, o CRM, workflows do n8n ou credenciais sem pedido explícito. O MCP do n8n é somente leitura.
- Não apagar nem sobrescrever arquivos; mover ou copiar para `mesa-certa-teste-dev/` (fora do pacote) e registrar.
- Não disparar webhook, executar workflow ou criar negócio no CRM sem autorização na mesma conversa. Um envio de teste por vez, sem retry automático.
- Nunca fazer commit, push, `reset`, `clean` ou reescrever o histórico git sem pedido explícito.

## 3. Qualidade das evidências

- Só afirmar o que foi executado e conferido. Cada prova cita ID da execução, horário e o estado do CRM e do SQLite antes e depois, lidos de forma independente do log da ferramenta.
- Dizer sempre o caminho exato que foi testado e o que não foi. Hoje: WF01 (execução 355, lead comercial), WF02 (execução 356, vínculo de negócio existente).
- Print não é prova obrigatória quando JSON, relatório e estado do CRM comprovam a execução.
- Não apresentar teste manual como agendamento automático. O agendamento do WF03 não está comprovado.

## 4. Validação de indicadores

- Todo cálculo recebe a data de referência como parâmetro. Nada de contagem fixa no código.
- Referência histórica validada, 12/10/2026 08:00: funil 391 (106 Novo, 133 Contato, 43 Reunião marcada, 37 Reunião realizada, 72 Perdido), 187 atualizados, 142 criados, 136 pedidos comerciais, 12 sem correspondência, 68 sem retorno vencido. Qualquer mudança que altere esses números exige explicação; nunca ajustar para "bater".
- Não confundir negócios atualizados com pedidos. Não usar negócios dos testes de 28 e 29/10 nos indicadores históricos.
- Conferir fusos (UTC x Brasília) e usar horas úteis (seg a sex, 8h às 18h) para o prazo de 4 horas.
- Não atribuir atraso a um SDR sem evidência: o banco não registra quem fez o contato.

## 5. Limitações a documentar sempre

- A cópia SQLite do CRM está desatualizada (último registro em 11/10); relatórios operacionais atuais exigem atualizá-la.
- A classificação de pedidos é uma regra por texto, sem revisão humana. O WF01 e `resumo_semanal.py` têm regras de níveis diferentes.
- Cenários sem execução: suporte, reenvio do mesmo pedido, assinatura inválida, falhas 429/500, criação pela conciliação e lote completo.

## 6. Sugestão de IA x decisão humana

- A IA sugere, executa o que foi autorizado e registra; a decisão é da autora. Ações feitas à mão (editor do n8n, reinícios, importação, cliques de execução, envio de e-mail, remoção de prints) não são atribuídas à IA.
- No `log-de-decisoes.md`, marcar cada sugestão como **[aceita]**, **[rejeitada]** ou **[revisada após teste]**, com data e horário.
- Em dúvida entre agir e perguntar, perguntar. Proposta de mudança em arquivo de terceiros ou do desafio vem como proposta, não como edição.

## 7. Ferramentas do projeto

- Auditoria de workflows: skill `auditoria-workflow-crm` (`/auditoria-workflow-crm`).
- Checagem de publicação: hooks `PostFileSave` e `PostFileCreate` (`.kiro/hooks/`) chamam `.kiro/scripts/verificar_publicacao.py`; só leem arquivos e avisam.
- Descrição do pacote: `.kiro/README.md`.
