# Problemas Identificados — Teste Técnico Mesa Certa

## 1. Objetivo

Documentar os problemas encontrados durante o desenvolvimento
da integração entre os webhooks de marketing e o CRM.

Os problemas estão organizados por prioridade, considerando
segurança, integridade dos dados e confiabilidade.

## 2. Problemas identificados

### P01 — Validação da assinatura HMAC

**Prioridade:** Crítica

**Problema:**
É necessário verificar se os eventos recebidos realmente
foram enviados por uma origem autorizada.

**Solução adotada:**
Implementar validação HMAC utilizando JavaScript no n8n.

**Dificuldade encontrada:**
O módulo crypto estava inicialmente bloqueado no ambiente.

**Resultado:**
A validação foi executada com sucesso para um evento de teste
(`evt_500110`). O HMAC precisa ser calculado sobre o corpo bruto
(opção Raw Body do Webhook); calculado sobre o JSON já lido pelo
n8n, os acentos mudam e a assinatura não bate.

**Pendente:**
Testar assinaturas inválidas e garantir a resposta HTTP adequada.
O lote tem 3 entregas com assinatura inválida
(`evt_500188`, `evt_500200`, `evt_500244`) para esse teste.

---

### P02 — Duplicidade de contatos no CRM

**Prioridade:** Alta

**Problema:**
O mesmo contato pode aparecer em diferentes eventos.

**Solução adotada:**
Consultar o CRM pelo e-mail antes de criar um novo negócio.

**Resultado:**
Foi possível identificar um contato já existente e evitar
uma nova tentativa de criação nesse teste.

**Limitações:**
A verificação por e-mail ainda não garante proteção completa
contra eventos repetidos ou processamento simultâneo.

---

### P03 — Normalização dos dados

**Prioridade:** Alta

**Problema:**
Os eventos podem conter diferenças de formatação, como
espaços adicionais e letras maiúsculas nos e-mails.

**Solução planejada:**
Padronizar os dados antes de consultar ou atualizar o CRM.

**Status:**
Pendente de implementação e validação completa.

---

### P04 — Falhas e instabilidade do CRM

**Prioridade:** Crítica

**Problema:**
O CRM simulado pode apresentar respostas HTTP 429 e 500,
atrasos e respostas HTTP 200 contendo indicação de erro.

Algumas falhas podem ocorrer mesmo após o registro
ter sido gravado no CRM.

**Solução planejada:**
Implementar tentativas controladas de reenvio,
intervalos progressivos e confirmação do estado do CRM.

**Status:**
Pendente.

---

### P05 — Idempotência dos eventos

**Prioridade:** Alta

**Problema:**
O mesmo evento pode ser enviado mais de uma vez.

**Solução planejada:**
Registrar identificadores dos eventos processados
e impedir que reenvios produzam efeitos duplicados.

**Status:**
Pendente.

---

### P06 — Classificação dos eventos

**Prioridade:** Média

**Problema:**
Nem toda mensagem recebida representa uma solicitação
válida de demonstração.

**Solução planejada:**
Separar solicitações comerciais de mensagens de teste,
suporte e outros eventos que não devem gerar novos negócios.

**Status:**
Pendente.

---

### P07 — Validação da criação de contatos

**Prioridade:** Alta

**Problema:**
O nó HTTP POST foi configurado, mas ainda não existe
confirmação de uma criação bem-sucedida de ponta a ponta.

**Resultado (28/10/2026):**
O evento `evt_500110` (João Almeida) criou o negócio 20392 no CRM.
Na consulta seguinte o CRM devolveu `total: 1` e o fluxo não
criou outro negócio. Prints e estado do CRM em `solucao/evidencias/`.

**Status:**
Testado com 1 evento. Falta testar o lote completo.

## 3. Ordem de resolução

A ordem de trabalho adotada ou planejada é:

1. Validar a autenticidade dos eventos.
2. Preparar e normalizar os dados.
3. Classificar os eventos recebidos.
4. Evitar duplicidades.
5. Criar ou atualizar os registros necessários.
6. Tratar falhas e reenvios.
7. Confirmar os resultados diretamente no CRM.
8. Registrar evidências da execução final.

Essa ordem poderá ser ajustada conforme os testes.

## 4. Decisões de escopo

Até o momento, não há uma decisão definitiva de excluir
algum requisito identificado.

Funcionalidades ainda não implementadas estão registradas
como pendentes, e não como descartadas.

Caso alguma alternativa seja rejeitada, serão documentados
o motivo, o impacto e a decisão correspondente.

## 5. Critérios para considerar a solução concluída

A solução deverá demonstrar:

- Validação correta de eventos legítimos e inválidos.
- Tratamento adequado de contatos existentes.
- Criação correta de novos registros.
- Proteção contra processamento duplicado.
- Tratamento das falhas simuladas pelo CRM.
- Evidências verificáveis do estado final do CRM.

## 6. Estado atual

Documento inicial baseado nos problemas encontrados
durante o desenvolvimento.

Será atualizado conforme novas validações forem realizadas.