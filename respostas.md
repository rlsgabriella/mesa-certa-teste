# Respostas para a gestora

Posição: **segunda-feira, 12/10/2026, 08:00 (horário de Brasília)**. Semana: de segunda 05/10 às 00:00 até domingo 11/10 às 23:59.
Cada resposta separa o que é **fato** (lido direto dos dados), **estimativa** (depende de uma regra minha) e **limite** (o que os dados não permitem dizer).
Os números foram conferidos em [uma validação](solucao/evidencias/04-workflow-03/validacao-resumo-semanal-2026-10-12.md) (23 de 23 batem). Detalhes em [`solucao/evidencias/`](solucao/evidencias/README.md).

## 1. Como está o time (negócios por etapa)

| Etapa | Negócios |
|---|---|
| Novo | 106 |
| Contato | 133 |
| Reunião marcada | 43 |
| Reunião realizada | 37 |
| Perdido | 72 |
| **Total** | **391** |

- **Fato:** 80 negócios já viraram reunião (marcada ou realizada).
- **Fato:** 22 dos 72 perdidos foram movidos pela limpeza automática em 06/10, às 02:14, e 20 perdidos nunca tiveram um primeiro contato.
- **Fato:** dos 106 em Novo, 7 são de agosto, 13 de setembro e 86 de outubro; os mais antigos estão parados há semanas.

## 2. Qual é o número certo de pedidos de demonstração?

**Por que deu 187 na sua planilha:** esse número bate dia a dia com a quantidade de negócios que tiveram a **última atualização** na semana (18, 45, 21, 24, 27, 28 e 24). Ele soma:

- 142 negócios **criados** na semana (133 vindos do site e 9 cadastrados manualmente);
- 45 negócios **antigos** que só foram mexidos na semana. Em 06/10 a limpeza automática mexeu em 22 deles, e é por isso que o dia 06 tem 45.

Ou seja, o 187 mede movimento no CRM, não pedidos de demonstração. **Fato.**

**Pedidos de demonstração recebidos pelo formulário na semana: 136** (**estimativa**), vindos de 111 pessoas. 18 pessoas pediram mais de uma vez.
O formulário recebeu 175 pedidos diferentes; os outros 39 são suporte (8), fornecedor (6), teste (13), lixo (7), spam (2) e pedidos com assinatura inválida (3), que não valem.
Considerei "demonstração" qualquer pedido que não seja um desses; "Quero testar o sistema" conta como demonstração.

Dos 142 negócios criados: 99 vieram de pedidos de demonstração, 27 de pedidos que não eram venda, 9 foram cadastrados à mão e 7 não têm pedido nos dados (explicado abaixo).

**Qual número o marketing usou?** Não sei. Duas hipóteses, **não confirmadas**: 175 (todos os pedidos diferentes, inclusive teste e lixo) ou 189 (conta também os reenvios do mesmo pedido).
Sugestão para a reunião: "187 é movimento no CRM; foram 136 pedidos de demonstração do formulário, de 111 pessoas".

**Limites:** os dados do formulário vão até domingo 11/10 às 18:16; 7 negócios foram criados depois disso e não têm pedido para comparar. A classificação dos pedidos é por texto e não foi revisada por pessoas.
O horário do formulário vem em UTC e foi convertido para Brasília; 9 pedidos entre 21h e 23h59 de 04/10 pertencem à semana anterior.

## 3. Quem está atrasando e quem está sem retorno hoje

**Regra usada:** ligar em até 4 horas úteis (segunda a sexta, 8h às 18h), contadas do cadastro do negócio até o primeiro contato registrado.
Pedido que chega no fim de semana ou depois das 18h só começa a contar na manhã seguinte útil.

**Negócios criados na semana a partir de pedidos de demonstração (estimativa): 99.**

- 46 foram atendidos no prazo e 16 fora do prazo.
- 13 estão sem retorno e já passaram do prazo; 24 estão sem retorno, mas ainda dentro do prazo.
- Dos 75 casos que já dá para julgar, **61% foram no prazo** (a faixa possível vai de 50% a 72%). O tempo típico até a ligação foi de 2,1 horas úteis, e 9 em cada 10 foram atendidos em até 4,7 horas úteis.

| Responsável pelo negócio | No prazo | Já julgados | Sem retorno vencido |
|---|---|---|---|
| SDR 1 | 17 | 28 (61%) | 5 |
| SDR 2 | 12 | 24 (50%) | 7 |
| SDR 3 | 17 | 23 (74%) | 1 |

**Isso prova que o SDR 2 é mais lento? Não.** O SDR 2 tem o menor percentual, mas a diferença pode ser acaso (a chance de ver uma diferença assim sem haver diferença real é de cerca de 21%).
Além disso, a tabela mostra quem é o **responsável** pelo negócio, não quem ligou: nos 35 negócios em que dá para ver quem registrou o contato, o responsável foi o autor em apenas 14.
Para cobrar alguém, é preciso saber quem de fato ligou.

**Sem retorno agora (12/10, 08:00):** dos 106 negócios em Novo, **nenhum teve contato** e **68 já passaram do prazo**. Por responsável: SDR 1 com 18, SDR 2 com 27 e SDR 3 com 23.
Desses 68, 47 vieram de pedidos de demonstração, 12 não têm pedido nos dados (11 antigos de agosto e setembro e 1 cadastrado à mão), 5 são teste e 4 são suporte.
**Para cobrar hoje: 59** (os 47 mais os 12 sem pedido). Entre os 68 vencidos, 11 esperam há mais de 100 horas úteis. A lista completa está no [arquivo da semana](solucao/evidencias/04-workflow-03/resumo-semanal-2026-10-12.json).

**Limites:** não sei de contatos feitos depois de 12/10 às 8h; 49 contatos registrados têm hora fora do expediente; feriados não são descontados.

## 4. Pedidos que não chegaram ao CRM e a fila que não é venda

Cruzei cada pedido de demonstração com os negócios pelo e-mail ou pelo telefone. Dos 136 pedidos:

- 99 viraram negócio (em até 20 segundos);
- 25 eram de pessoas que já tinham negócio (mesmo e-mail ou telefone, negócio criado antes do pedido);
- **12 não aparecem no CRM** (10 pessoas, **estimativa**), todos com assinatura válida:

| Pedido | Quando pediu (Brasília) | Nome | Telefone |
|---|---|---|---|
| evt_500110 | 05/10 00:42 | João Almeida | (31)976637920 |
| evt_500127 | 05/10 14:24 | Fábio Teixeira | (61)932001790 |
| evt_500154 | 06/10 14:05 | Raquel Rocha | +5581911628421 |
| evt_500158 | 06/10 15:43 | Aline Barbosa | (71)991886327 |
| evt_500187 | 07/10 14:23 | Thiago Costa | (11) 92474-3787 |
| evt_500191 | 07/10 15:38 | Juliana Cavalcanti | 19911938637 |
| evt_500194 | 07/10 18:23 | Diego Martins | +55 47 94332-1351 |
| evt_500198 | 07/10 23:50 | Larissa Santos | 31976637920 |
| evt_500236 | 09/10 10:18 | Sérgio Rocha | 47 97030 4750 |
| evt_500260 | 10/10 09:33 | Adriana Martins | +5519922074618 |
| evt_500269 | 10/10 14:20 | Débora Martins | 71963641471 |
| evt_500279 | 11/10 11:13 | José Ribeiro | (47) 7030-4750 |

Pelo telefone, Sérgio Rocha e José Ribeiro parecem a mesma pessoa, e João Almeida e Larissa Santos usam o mesmo número com nomes diferentes.
João Almeida foi usado num teste de 28/10 e hoje tem o negócio 20392 no CRM de teste; os outros 11 continuam sem negócio. Não criei nenhum deles no CRM.
**Limite:** não sei por que faltam. Pode ser falha da integração antiga ou cadastro manual com outros dados; os dados não distinguem.

**A fila que não é venda (fato):** 28 pedidos que não eram venda geraram 27 negócios no CRM: suporte 8, fornecedor 5, teste 10, spam 1 e lixo provável 3.
Os 3 pedidos com assinatura inválida não geraram negócio.

## 5. Resumo toda segunda de manhã

- **Pronto:** o cálculo e o texto do resumo (exemplo de 12/10 em [`resumo-semanal-2026-10-12.txt`](solucao/evidencias/04-workflow-03/resumo-semanal-2026-10-12.txt)), com 25 testes automáticos aprovados. Um e-mail de teste, enviado manualmente em 29/10 às 14:53, chegou ao Gmail.
- **Executado no n8n:** o fluxo roda de ponta a ponta quando acionado à mão (execuções 357 e 359, e-mail aceito pelo SMTP).
- **Agendamento observado:** em 29/10 às 16:50 o n8n disparou o resumo sozinho (execução 361, modo agendado) e o e-mail chegou. Foi um teste com horário diário.
- **Não comprovado:** a segunda às 8h em si. Falta voltar o horário do teste para segunda 08:00 e ativar o workflow, que hoje está inativo.
- **Atenção:** o e-mail de teste de 29/10 saiu com a cópia do CRM desatualizada (último registro em 11/10), então mostrava zero negócios na semana e trazia um aviso. Para um relatório operacional atual, essa cópia precisa ser atualizada a partir do CRM antes de cada envio.
- **Não feito:** poder perguntar e receber resposta.

## O que os dados não permitem afirmar

- O número que o marketing apresentou e a causa dos 12 pedidos ausentes.
- Quem fez cada ligação e, por isso, quem atrasa.
- Se os contatos aconteceram depois de 12/10 às 8h.
- Que a classificação de suporte, fornecedor, teste e lixo esteja certa em todos os casos.
- Que o resumo automático funciona toda segunda sem ajuda.
