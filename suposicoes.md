# Suposições — Teste Técnico Mesa Certa

## 1. Contexto

O desafio estabelece como referência o dia
12/10, às 08:00, no horário de Brasília.

Como não é permitido consultar a gestora,
as decisões precisam ser documentadas e
validadas com os dados disponíveis.

## 2. Suposições adotadas

### Identificação dos clientes
O e-mail normalizado será utilizado como
identificador principal para consultar
registros no CRM.

O telefone será utilizado como informação
complementar.

Conflitos de identidade serão encaminhados
para revisão manual.

### Pedidos duplicados
Reenvios com o mesmo event_id não deverão
gerar novos registros.

Antes de criar um negócio, o sistema deverá
consultar se ele já existe no CRM.

### Pedidos de teste e spam
Pedidos suspeitos serão classificados para
revisão manual, sem exclusão automática.

### Horário comercial
O prazo de primeiro contato será calculado
considerando segunda a sexta-feira,
das 08:00 às 18:00, horário de Brasília.

Na ausência de uma regra explícita, feriados
não serão descontados automaticamente.
Essa hipótese precisa ser documentada
nos resultados.

### Segurança
Os dados originais devem ser preservados.
Testes devem utilizar ambientes isolados
sempre que possível.

### Recuperação de pedidos
O levantamento de pedidos ausentes será
feito inicialmente em modo dry-run,
sem criar novos negócios no CRM.

## 3. Perguntas para a gestora

1. O prazo de quatro horas comerciais
   considera feriados nacionais e locais?

2. Qual evento comprova que o SDR realizou
   o primeiro contato com o cliente?

3. Como devemos tratar clientes que enviam
   mais de um pedido de demonstração?

4. Quais critérios a equipe utiliza para
   distinguir oportunidades comerciais
   de suporte, fornecedores e testes?

5. Quais indicadores são indispensáveis
   no resumo semanal e por qual canal
   você prefere recebê-lo?