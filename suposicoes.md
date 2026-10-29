# Suposições

Não foi possível perguntar à gestora. Estas são as hipóteses adotadas, com a justificativa, e as cinco perguntas que eu faria.
Os resultados que dependem delas estão marcados como **estimativa** em [`respostas.md`](respostas.md).

## Hipóteses adotadas

| # | Hipótese | Justificativa |
|---|---|---|
| 1 | "Hoje" é segunda 12/10/2026, 08:00, horário de Brasília; a semana vai de segunda 00:00 a domingo 23:59. | Definido no enunciado e na fala dela (de segunda dia 5 a domingo dia 11). |
| 2 | O horário do formulário e do webhook é UTC e foi convertido para Brasília (UTC-3). O CRM e o histórico já estão em Brasília. | O enunciado informa os fusos. A conversão foi confirmada: os negócios nascem de 2 a 20 segundos depois do pedido convertido. |
| 3 | "Pedido de demonstração" é todo pedido que não é suporte, fornecedor, teste, lixo, spam nem assinatura inválida, segundo uma regra por texto, nome e e-mail. "Quero testar o sistema" é comercial. | A fala dela cita suporte, fornecedor e teste como ruído. A regra antiga marcava "testar" como teste e errava 5 pedidos. |
| 4 | Mesma pessoa = mesmo e-mail (sem espaços, em minúsculas) ou mesmo telefone (só dígitos, sem o 55). | Os pedidos trazem e-mails com espaço e maiúsculas e telefones em sete formatos. |
| 5 | Pedido "sem correspondência" é o pedido comercial sem negócio com o mesmo e-mail ou telefone criado a partir de 60 segundos antes do pedido. | O CRM cria o negócio segundos depois do pedido. |
| 6 | O prazo é de 4 horas úteis, de segunda a sexta, das 8h às 18h, contado do cadastro do negócio até o campo `primeiro_contato_em`. Feriados não são descontados. | É a regra citada por ela. O cadastro ocorre segundos após o pedido, então a diferença de partida é desprezível. |
| 7 | "Sem retorno" é o negócio em Novo, sem primeiro contato até a data de referência. Perdido fica fora. | É o que ela quer cobrar "hoje". |
| 8 | Pedidos com o mesmo `event_id` são o mesmo pedido; assinatura inválida não conta como pedido. | O remetente reenvia até 4 vezes (documentação do webhook), e o lote traz 3 entregas com assinatura inválida. |
| 9 | Os dados originais ficam intactos; os testes usam cópias e o CRM de teste. Os negócios criados nos testes de 28 e 29/10 não entram nos números históricos. | Permite repetir a análise do zero. |
| 10 | Os valores de segredo e de token no material do desafio são de teste e não são credenciais reais. Como o repositório é público, tratei o segredo como exposto. | Estão no próprio material do desafio; a cautela vale porque um commit antigo os publicou. |
| 11 | A cópia SQLite do CRM (`negocios_crm`) vale como o estado de 12/10 e não foi atualizada depois. | O banco do enunciado reflete esse momento; nenhum processo a atualiza. |
| 12 | Não reclassificar os 104 pedidos antigos nem alterar o CRM sem autorização dela. | Evita mudar dados sem aval de quem é dona do processo. |

## Perguntas que eu faria à gestora

1. O prazo de quatro horas úteis desconta feriados nacionais e locais?
2. O que prova que o SDR fez o primeiro contato, e quem deve registrá-lo no CRM?
3. Quando a mesma pessoa pede demonstração mais de uma vez, conta como um pedido ou como vários?
4. Quais critérios o time usa para separar pedido de venda de suporte, fornecedor e teste, e esses itens devem sair da fila do time?
5. Quais indicadores são indispensáveis no resumo de segunda, e por qual canal (e-mail ou Slack) e para quem?
