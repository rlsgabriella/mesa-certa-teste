# Scripts de indicadores (resumo semanal)

Calculam os números da gestora (funil, pedidos da semana, pedidos que não chegaram ao CRM, prazo de primeiro contato, quem está sem retorno) e montam o resumo em linguagem simples. Só usam a biblioteca padrão do Python 3.10+; não gravam no banco, não chamam o CRM, não disparam webhook.

| Arquivo | Para quê |
|---|---|
| `resumo_semanal.py` | Calcula os indicadores. Lê o SQLite em `mode=ro`. Gera JSON e texto, ou sobe um serviço local para o n8n. |
| `test_resumo_semanal.py` | 25 testes automáticos com bancos temporários. |
| `validar_resumo_historico.py` | Roda o cálculo sobre uma **cópia** de `mesa_certa.original.db` para 12/10/2026 08:00 e compara com a apuração histórica. |

## Uso

```powershell
# resumo da semana anterior a uma data (Brasília); sem --ref usa "agora"
py solucao\scripts\resumo_semanal.py --ref "2026-10-12 08:00" --saida texto

# reproduzir 12/10/2026 com o lote do webhook (segredo só na sessão, para conferir as assinaturas)
$env:MESA_CERTA_HMAC_SECRET = "<segredo do desafio>"
py solucao\scripts\resumo_semanal.py --db mesa_certa.original.db --lote webhook\lote-webhook.jsonl `
   --ref "2026-10-12 08:00" --json-out resumo.json --txt-out resumo.txt --saida nenhuma

# testes e validação histórica
py -m unittest solucao/scripts/test_resumo_semanal.py -v
py solucao\scripts\validar_resumo_historico.py --saida-dir solucao\evidencias\04-workflow-03

# serviço local para o WF03 (somente leitura, 127.0.0.1)
py solucao\scripts\resumo_semanal.py --servir --porta 8002 --db mesa_certa.db
```

O serviço responde `GET /saude` e `GET /resumo?ref=AAAA-MM-DDTHH:MM`. Para ficar sempre no ar, é preciso registrá-lo como tarefa do Windows (não feito). Horários em Brasília; `pedidos_formulario.criado_em` e o lote estão em UTC e são convertidos.

## O que sai (JSON)

`indicadores_comprovados` (leitura direta dos dados), `estimativas` (dependem da classificação por texto e do cruzamento por e-mail/telefone), `dados_incompletos`, `limitacoes` e `resumo_texto` (o texto para a gestora).

## Definições

- **Funil:** última etapa do `historico_etapas` até a referência, só para negócios criados até ela.
- **Atualizados:** `atualizado_em` no período. Reproduz o 187 da planilha; **não** conta pedidos.
- **Pedido comercial:** regra por texto, nome e e-mail (`classificar_pedido`). "Quero testar o sistema" é comercial.
- **Sem correspondência:** pedido comercial sem negócio com o mesmo e-mail ou telefone, criado a partir de 60 s antes do pedido.
- **Prazo:** horas úteis (seg a sex, 8h às 18h), limite de 4 h. "Sem retorno e vencido": sem contato e mais de 4 h úteis até a referência (Perdido fica fora).

## Validação (12/10/2026 08:00)

**23 de 23 indicadores conferem** com a apuração histórica (funil 391, 187 atualizados, 142 criados, 136 pedidos comerciais, 12 sem correspondência, 68 sem retorno vencido e mais 17 de apoio). Original e cópia ficaram com o mesmo SHA-256. Única diferença de definição: mediana de 2,08 h úteis aqui contra 2,15 na apuração anterior. Relatório em `solucao/evidencias/04-workflow-03/validacao-resumo-semanal-2026-10-12.md`. Os pedidos só batem com o lote usando a cópia do original, porque o `mesa_certa.db` de trabalho tem o `evt_500110` repetido do teste de 28/10.

## WF03 e o que falta para ativar

Estado e provas (execuções 357, 359 e 361): `solucao/evidencias/04-workflow-03/wf03-execucao-361-agendada.md`. Falta:

1. **Atualizar `negocios_crm`.** A cópia vai até 11/10 e nada a atualiza; sem isso o resumo avisa "banco desatualizado".
2. **Manter o serviço no ar** na porta 8002 e o n8n ligado na segunda às 08:00.
3. **Ativar o workflow** (cron em segunda 08:00 e fuso `America/Sao_Paulo` já configurados).
4. **Definir** canal (e-mail ou Slack) e destinatário (`RESUMO_SEMANAL_DESTINATARIO`, `RESUMO_SEMANAL_REMETENTE`).
