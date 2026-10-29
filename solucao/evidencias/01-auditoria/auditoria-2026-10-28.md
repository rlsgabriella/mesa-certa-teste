# Auditoria dos dados e do repositório — 28/10/2026

Feita entre 00:59 e 01:10 (horário de Brasília) de 28/10/2026, só com leitura.
Nenhum banco, arquivo original ou dado do CRM foi alterado.

Base de cálculo: `mesa_certa.original.db` e `webhook/lote-webhook.jsonl` do
desafio. Os scripts usados (`mc_*.py`, todos de leitura) e a implementação
Python antiga estão no arquivo `arquivo-python-2026-10-28.zip`, fora do repositório.

"Semana" = 05/10 00:00 a 11/10 23:59, horário de Brasília.

---

## 1. Integridade

| Verificação | Resultado |
|---|---|
| `mesa_certa.db` e `mesa_certa.original.db` × `candidato.zip` original | Idênticos (SHA-256 começa com `F545271F6CC9`). |
| `crm-mock-teste/crm-mock.py` e `crm-seed.json` × `candidato.zip` | Idênticos. |
| Conteúdo dos bancos | Só as 3 tabelas do desafio (`negocios_crm`, `historico_etapas`, `pedidos_formulario`). Nenhuma coluna de CPF, CNPJ, endereço, senha ou token. A empresa e os clientes são fictícios segundo o `enunciado.md`. |
| Teste do João Almeida | Negócio `20392`, criado em 28/10/2026 00:33:11 no CRM mock (392 negócios no total). Cópia do estado em `../02-workflow-01/crm-estado-teste-joao-almeida-20392.json`. |

## 2. Números confirmados

Cada número abaixo foi calculado por script e conferido.

### CRM (estado de 12/10 08:00)
- 391 negócios: Contato 133, Novo 106, Perdido 72, Reunião marcada 43, Reunião realizada 37.
- Criados na semana (por `criado_em`): **142**. Por dia, de 05 a 11/10: 22, 25, 20, 20, 24, 13, 18.
  Desses, 9 têm origem "Manual" (criados por SDR, não pelo formulário).
- A planilha da gestora (18, 45, 21, 24, 27, 28, 24 = **187**) bate nos 7 dias
  com a contagem por **`atualizado_em`** (data da última atualização).
- Pico de 06/10: entre 02:14:01 e 02:14:39, a `automacao_limpeza` moveu
  22 negócios antigos (criados de 05/08 a 22/09) para Perdido.
- 10 e-mails têm mais de um negócio, todos criados na semana. 4 são e-mails de
  teste (`dev.teste@mesacerta.com.br`, `teste@mesacerta.com.br`,
  `teste123@gmail.com`, `teste@teste.com`).
- 106 negócios em Novo: `sdr_1` 27, `sdr_2` 43, `sdr_3` 36. Por mês de criação:
  agosto 7, setembro 13, outubro 86.
- 20 negócios estão em Perdido sem `primeiro_contato_em`
  (7 movidos pela `automacao_limpeza`, 4 por `sdr_1`, 4 por `sdr_2`, 5 por `sdr_3`).
- `pedidos_formulario` tem 100 registros, só de 28/09 a 04/10.

### Lote do webhook
- 201 entregas: 196 válidas, 3 com assinatura inválida
  (`evt_500188`, `evt_500200`, `evt_500244`), 2 com JSON quebrado.
- 184 `event_id` distintos; 181 com assinatura válida.
- Na semana: 189 entregas, 175 `event_id` distintos, 14 reenviados.
  Com assinatura válida: 172.
- Pelo `webhook/README.md`, o lote vai de 05/10 00:00 UTC a 12/10 00:00 UTC.
  Isso inclui 9 eventos de 04/10 21:00–23:59 (Brasília) e **não** cobre
  11/10 de 21:00 a 23:59 (Brasília).

### Conciliação com a regra antiga (`conciliar_revisado.py`)
Essa regra não confere assinatura e usa a classificação antiga.
- 175 da semana = 20 teste + 1 spam + 154 legítimos.
- Dos 154: 124 ligados a negócio criado na semana, 11 só a negócio antigo,
  **19 sem correspondência** (cruzando por e-mail ou telefone).
- O dry-run (`dryrun_resultado.txt`) mostrou 21 sem correspondência porque
  cruzou só por e-mail. `evt_500148` e `evt_500190` batem pelo telefone.
- Dos 19, 3 têm assinatura inválida. Com assinatura válida: **16**.
- 5 pedidos comerciais ("Quero testar o sistema de vocês. Como começo?") foram
  classificados como teste por engano: `evt_500177`, `evt_500183`,
  `evt_500184`, `evt_500185`, `evt_500198`.
- 2 eventos têm e-mail e telefone apontando para negócios diferentes.
- 32 negócios estão ligados a mais de um evento legítimo da semana.

## 3. Hipóteses (não confirmadas)

| Hipótese | O que falta para confirmar |
|---|---|
| O número do marketing é 189 (entregas) ou 175 (eventos distintos). | Não sabemos qual número o marketing apresentou. |
| Os 16 pedidos sem correspondência são falhas da integração antiga. | Podem ter outros motivos (cadastro manual com outro e-mail, por exemplo). Precisa olhar caso a caso. |
| Parte das reclamações de "ninguém retornou" vem de negócios fechados sem contato pela `automacao_limpeza`. | Cruzar com as reclamações dos clientes, que não estão nos dados. |
| Os e-mails duplicados no CRM foram criados pela integração antiga. | O banco não guarda quem criou o negócio; `atualizado_por` só mostra a última alteração. |
| O `sdr_2` é mais lento. | O SLA ainda não foi calculado. Ter mais negócios em Novo (43) **não** prova atraso. |
| As contagens finais de teste, spam, suporte e fornecedor. | Dependem da regra de classificação nova (`../../../como-assumir.md`, "Regras que o código implementa"). |

## 4. Situação do repositório antes da limpeza

- A pasta `solucao/` tinha a implementação Python (receptor, worker, cliente do
  CRM, 22 testes) e scripts de exploração. Foi arquivada, ver `log-de-decisoes.md`.
- `respostas.md`, `como-assumir.md`, `guia-para-ela.md` e `quando-usar-o-que.md` estavam vazios.
- O repositório git não tem nenhum commit.
