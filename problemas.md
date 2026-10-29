# Problemas identificados

Fonte: a mensagem de voz da gestora (transcrita em [`enunciado.md`](enunciado.md)) e o que os dados mostraram.
Referência de tempo: segunda-feira, 12/10/2026, 08:00 (Brasília). Semana analisada: 05/10 a 11/10.
Status em 29/10/2026. Os números vêm das [evidências](solucao/evidencias/README.md); a regra de classificação dos pedidos é uma estimativa.

## Resumo

| # | Problema (como ela falou) | Prioridade | Ordem | Status |
|---|---|---|---|---|
| P1 | Pedidos do marketing entram com erro, repetidos ou sem segurança | Crítica | 2.º | Resolvido nos caminhos testados (Workflow 01) |
| P2 | "Pedidos que eu nunca vi chegar no CRM" | Alta | 3.º | Identificado (12 pedidos); evitar novos: Workflow 02 testado só no caminho de vincular |
| P3 | "187 ou o número do marketing?" | Alta | 4.º | Explicado; número do marketing desconhecido |
| P4 | "Quem está atrasando? Quem está sem retorno hoje?" | Alta | 4.º | Calculado; sem base para apontar um SDR |
| P5 | "Como está o time" (negócios por etapa) | Média | 4.º | Calculado e validado para 12/10 |
| P6 | Fila com suporte, fornecedor e teste | Média | 4.º | Medido (27 negócios); limpeza não feita |
| P7 | Resumo toda segunda, sem pedir a ninguém | Média | 5.º | Cálculo e texto prontos; disparo agendado observado em teste (exec. 361); horário de segunda 08:00 configurado; fluxo inativo até alguém ativar |
| P8 | Time não pode mudar o jeito de usar o CRM | Restrição | todas | Respeitada no desenho; não validada com o time |
| P9 | "Perguntar depois e ele responder" | Baixa | não feito | Adiado |

## Ordem de resolução e por quê

1. **Entender os dados antes de automatizar (27 e 28/10).** Sem isso não havia como saber se 187 estava certo. Resultado: o 187 conta negócios por data de atualização, e a base mistura pedidos comerciais com suporte, fornecedor e teste.
2. **Receber os pedidos com segurança (P1, Workflow 01).** Era o que mais podia causar dano (assinatura falsa, pedido repetido, negócio duplicado). Aprovado na execução 355 para um lead comercial.
3. **Conciliar o que ficou pendente (P2, Workflow 02).** Aprovado na execução 356 para vincular um negócio que já existia, sem duplicar.
4. **Apurar os números históricos (P3 a P6).** Feito sobre uma cópia do banco original e o lote do webhook, sem usar os negócios criados nos testes.
5. **Resumo semanal (P7, Workflow 03).** Por último, porque depende dos números anteriores.

## Detalhe

- **P1 Entrada dos pedidos.** O formulário assina cada pedido; o Workflow 01 confere a assinatura sobre o corpo exato, responde 200 antes de falar com o CRM, grava o pedido e só cria negócio para pedido comercial. Evidência: [execução 355](solucao/evidencias/02-workflow-01/t1-005-aprovado.md).
- **P2 Pedidos ausentes.** 12 pedidos comerciais da semana (10 pessoas) não têm negócio por e-mail nem telefone. Lista em [`respostas.md`](respostas.md). Não sabemos a causa.
- **P3 O 187.** É o número de negócios com atualização na semana: 142 criados mais 45 antigos mexidos, 22 deles pela limpeza automática. Pedidos de demonstração do formulário: 136 (estimativa).
- **P4 Prazo de 4 horas úteis.** 46 dos 99 negócios de pedidos comerciais foram atendidos no prazo, 16 fora, 13 vencidos sem retorno e 24 ainda dentro do prazo. Em 12/10 há 68 negócios em Novo com prazo vencido. A diferença entre SDRs não é estatisticamente comprovada e o banco não diz quem ligou.
- **P5 Funil.** 106 Novo, 133 Contato, 43 Reunião marcada, 37 Reunião realizada, 72 Perdido (391).
- **P6 Fila poluída.** 28 pedidos não comerciais viraram 27 negócios: suporte 8, fornecedor 5, teste 10, spam 1 e lixo provável 3.
- **P7 Resumo.** [Cálculo validado](solucao/evidencias/04-workflow-03/validacao-resumo-semanal-2026-10-12.md) (23 de 23) e 25 testes automatizados. Um e-mail de teste enviado manualmente em 29/10 chegou ao Gmail. O disparo agendado foi provado em teste (execução 361); o fluxo está configurado para segunda às 8h e inativo até alguém ativar.
- **P8 Não mudar o CRM.** O cadastro chega ao CRM pela API e o resumo vai por e-mail; nenhuma tela do CRM muda. Não houve teste com o time.

## O que foi adiado ou não resolvido, e por quê

| Item | Motivo |
|---|---|
| Assistente que responde perguntas (P9) | O enunciado a trata como desejo; priorizei números confiáveis e o resumo. |
| Criar no CRM os 12 pedidos ausentes | Criar negócio sem confirmar a causa pode duplicar; decisão da gestora. |
| Limpar os 27 negócios não comerciais e reclassificar os 104 pedidos antigos | Mexer no CRM e no histórico exige autorização; só medi. |
| Dizer quem atrasa | Sem base: amostra pequena e autoria do contato desconhecida. |
| Feriados no prazo | Sem regra informada (pergunta 1 em [`suposicoes.md`](suposicoes.md)). |
| Atualizar a cópia SQLite do CRM | Nenhum processo faz isso; é pré-requisito para relatórios operacionais atuais. |
| Agendar o Workflow 02 | O gatilho é manual; a conciliação ainda não é automática. |
| Validar a classificação de pedidos com pessoas | Regra por texto, sem revisão humana. |
| Cenários não executados | Suporte, reenvio do mesmo pedido, assinatura inválida, falhas do CRM, criação por conciliação e lote completo. |
