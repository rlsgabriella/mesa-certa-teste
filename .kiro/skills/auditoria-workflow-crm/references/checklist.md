# Checklist de auditoria: webhook, banco e CRM

Marque cada item como **ok**, **falha**, **não comprovado** ou **não se aplica**, com a fonte (nó, execução, consulta).

## Entrada
- [ ] Assinatura conferida sobre os bytes recebidos (webhook com corpo bruto ligado), com `timingSafeEqual` e checagem de tamanho.
- [ ] Assinatura inválida responde 4xx e não segue para banco nem CRM.
- [ ] Corpo que não é JSON e campos obrigatórios ausentes têm resposta definida (400).
- [ ] E-mail normalizado (minúsculas, sem espaços); telefone só com dígitos, sem DDI 55.
- [ ] Horários convertidos de UTC para Brasília antes de comparar com CRM e histórico.
- [ ] Nenhum `pinData` ou dado fixo de teste no workflow.

## Resposta ao remetente
- [ ] 2xx só depois de o evento estar gravado; resposta antes das chamadas lentas ao CRM.
- [ ] 5xx apenas para falha realmente reenviável; 4xx não é reenviado pelo remetente.

## Idempotência
- [ ] Chave do evento gravada com restrição de unicidade ou `NOT EXISTS`/`ON CONFLICT`.
- [ ] Reenvio do mesmo evento não cria nem atualiza nada duas vezes.
- [ ] Consulta ao CRM por e-mail antes de criar; `409` tratado como sucesso (usa o `deal_id` devolvido).
- [ ] POST que dá 500 pode ter gravado: consultar o CRM antes de repetir.
- [ ] `UPDATE` de estado só a partir do estado esperado (`WHERE estado = 'pendente'`).

## Erros
- [ ] 401/403 (configuração), 422/400 (dado inválido, sem retry), 429 (respeitar `Retry-After`), 5xx e timeout (retry com espera crescente).
- [ ] Resposta 200 com `"status": "erro"` não é sucesso.
- [ ] Todo nó com saída de erro habilitada tem destino; a falha é registrada e visível.
- [ ] Estado intermediário não fica preso (existe caminho para `falha` e para nova tentativa).

## Evidências
- [ ] Execução com ID, horário, nós executados e nós que não rodaram.
- [ ] Estado do CRM antes e depois conferido por consulta independente (contagem e registro).
- [ ] Banco conferido por consulta de leitura (linhas criadas, estado, ausência de duplicata).
- [ ] Caminhos não executados listados como **não comprovados**.
- [ ] Teste manual não é apresentado como execução agendada.

## Segurança
- [ ] Sem segredo, token ou senha no JSON, em `pinData`, em expressões ou em log.
- [ ] Credenciais por referência; ids das credenciais explicados para a reimportação.
- [ ] Dados pessoais nas provas limitados ao necessário.
