# Validação do resumo semanal: referência 12/10/2026 08:00 (Brasília)

Script: `solucao/scripts/resumo_semanal.py`, executado em modo somente leitura sobre uma **cópia** de `mesa_certa.original.db` com o lote `webhook/lote-webhook.jsonl`. Nenhum número foi ajustado.

**Resultado: 23 de 23 indicadores conferem; 0 divergem.**

| Indicador | Esperado | Obtido | Confere |
|---|---:|---:|:---:|
| Funil: total de negócios | 391 | 391 | sim |
| Funil: Novo | 106 | 106 | sim |
| Funil: Contato | 133 | 133 | sim |
| Funil: Reunião marcada | 43 | 43 | sim |
| Funil: Reunião realizada | 37 | 37 | sim |
| Funil: Perdido | 72 | 72 | sim |
| Negócios atualizados na semana (planilha: 187) | 187 | 187 | sim |
| Negócios criados na semana | 142 | 142 | sim |
| Pedidos comerciais identificados no lote | 136 | 136 | sim |
| Pedidos comerciais sem correspondência no CRM | 12 | 12 | sim |
| Negócios sem contato com prazo vencido (Novo) | 68 | 68 | sim |
| Pedidos distintos na semana (inclui 3 com assinatura inválida) | 175 | 175 | sim |
| Pessoas distintas entre os comerciais | 111 | 111 | sim |
| Comerciais que viraram negócio | 99 | 99 | sim |
| Comerciais de quem já tinha negócio | 25 | 25 | sim |
| Negócios de não comerciais no CRM (suporte+fornecedor+teste+spam+lixo) | 27 | 27 | sim |
| Prazo: negócios de pedido comercial criados na semana | 99 | 99 | sim |
| Prazo: contato dentro de 4 h úteis | 46 | 46 | sim |
| Prazo: contato atrasado | 16 | 16 | sim |
| Prazo: sem contato e vencido | 13 | 13 | sim |
| Sem retorno vencido que são pedidos comerciais | 47 | 47 | sim |
| Assinaturas inválidas no lote | 3 | 3 | sim |
| Entregas do lote com JSON inválido | 2 | 2 | sim |

## Integridade

- Original inalterado: True; cópia inalterada: True; cópia idêntica ao original: True.
- SHA-256 do original: `F545271F6CC9C8761188FE5275DF1BD878ED63E74965EF77642EDA37419540D6`.

## Nota

Mediana de horas úteis até o contato: este script usa a mediana estatística (média dos dois valores centrais quando o total é par): 2.08. A apuração de 29/10 usou o valor central superior (2,15). Não é divergência de dados, só de definição.

Arquivos gerados: `resumo-semanal-2026-10-12.json` (completo) e `resumo-semanal-2026-10-12.txt` (texto para a gestora).
