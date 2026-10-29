# WF03: execução agendada 361 (29/10/2026, 16:50)

Prova de que o Schedule Trigger do WF03 dispara sozinho. Dados lidos do n8n pelo MCP (somente leitura) e conferidos com a tela de execuções e o e-mail recebido, que estão nesta pasta: [execucao-automatica.png](execucao-automatica.png) (execução #361, 16:50:00) e [email-chega.png](email-chega.png) (e-mail das 16:50, com tarja sobre o nome do endereço).

| Item | Valor |
|---|---|
| Workflow | `wrGCERjaPYAeDcuH` (Mesa Certa\|03-Resumo Semanal da Gestora, 11 nós) |
| Execução | **361**, status `success`, modo **`trigger`** (não é clique manual) |
| Início e fim | 16:50:00,079 e 16:50:03,781 (Brasília); UTC 19:50:00 e 19:50:03; duração 3,7 s |
| Gatilho | cron `0 50 16 * * *`; o nó registrou 16:50:00 em `America/Sao_Paulo (UTC-03:00)` |
| Nós executados | gatilho, "Enviar e-mail" (resposta SMTP `250 2.0.0 OK`, um destinatário aceito, nenhum rejeitado) e "Registrar: resumo enviado" (`status: enviado`, 16:50:03) |
| Recebimento | a autora confirmou o e-mail no Gmail às 16:50; o resumo diz "posição em 29/10 às 16:50, horário de Brasília" (ver `email-chega.png`) |

## Como chegou aqui

1. 16:20: primeira tentativa **sem execução agendada**. O workflow estava inativo e a cópia importada não tinha fuso (`America/New_York`).
2. Correção manual da autora (Settings, Timezone `America/Sao_Paulo`) e nova publicação. Um erro "Invalid cron expression" apareceu porque a expressão tinha um ponto no fim (`0 50 16 * * *.`); depois de removido, a publicação passou.
3. 16:50: a execução 361 disparou no horário.

## O que isso prova e o que não prova

- **Prova:** o Schedule Trigger, no fuso de Brasília, dispara sem clique e percorre o fluxo até o envio de e-mail aceito pelo SMTP.
- **Escopo:** o teste usou um cron diário em outro horário, de propósito, para mostrar que o agendamento funciona independente do horário. O gatilho e o fuso são os mesmos do horário definitivo (segunda 08:00); a execução da própria segunda às 08:00 não foi esperada.
- **Dados do resumo:** continuam desatualizados. O e-mail dizia que a cópia do CRM só tem registros até 11/10/2026 e mostrava 0 negócios na semana; serve como teste de envio, não como visão da operação.
- **Estado depois do teste:** a autora devolveu o cron a segunda 08:00 (`0 0 8 * * 1`, conferido no n8n) e deixou o workflow **inativo**, sem necessidade de ativá-lo para a entrega. Para o envio semanal começar, basta ativá-lo.
