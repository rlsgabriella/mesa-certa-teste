# Pacote do assistente de IA (Kiro)

Item 6 do enunciado: instruções fixas, procedimento reutilizável e checagem automática, mais [`quando-usar-o-que.md`](../quando-usar-o-que.md). Os formatos e as pastas seguem a documentação do Kiro (*Steering*, *Agent Skills*, *Hooks*).

| Componente | Caminho | Quando é usado |
|---|---|---|
| Instruções persistentes (`inclusion: always`) | [`steering/mesa-certa-projeto.md`](steering/mesa-certa-projeto.md) | Em toda conversa neste projeto |
| Skill `auditoria-workflow-crm` | [`skills/auditoria-workflow-crm/`](skills/auditoria-workflow-crm/SKILL.md) | Quando o pedido combina com a descrição, ou com `/auditoria-workflow-crm` |
| Hooks `PostFileSave` e `PostFileCreate` | [`hooks/`](hooks/) | Quando o agente salva ou cria um arquivo de texto |

## O que cada um faz

- **Instruções:** segurança (nunca imprimir valor de segredo), preservação de dados (`mesa_certa.original.db` imutável, sem commit ou push sem pedido), evidências (só o que foi executado e conferido), validação de indicadores (data de referência como parâmetro, base histórica de 12/10/2026), limitações a documentar e separação entre sugestão da IA e decisão humana. O Kiro as injetou como regra do workspace, o que confirma o carregamento. `AGENTS.md` seria uma alternativa; não foi usado, para não duplicar.
- **Skill:** audita um workflow n8n/CRM em modo somente leitura (entradas, saídas, idempotência, erros, evidências, segurança) e gera relatório. Apoio: `references/checklist.md`, `references/modelo-relatorio.md` e `scripts/inspecionar_workflow.py`, que lê o JSON exportado sem executar nada.
  Uso: `/auditoria-workflow-crm Audite solucao/workflows/wf01-recebimento-cadastro-leads.json` ou `py .kiro/skills/auditoria-workflow-crm/scripts/inspecionar_workflow.py <workflow.json>`.
  Sobre o WF01 exportado: 0 alertas e 2 avisos ("Criar Negócio no CRM" sem retry; Code node com `console.log` do hash do segredo).
- **Hooks:** chamam `py .kiro/scripts/verificar_publicacao.py --stdin` (timeout 20 s). O script só lê, **nunca imprime valores** (mostra arquivo, linha e tipo: valor do `.env`, token do `crm-mock.py`, Bearer, JWT, chave privada, `.env` não ignorado pelo git) e **só avisa** (sai com 1 se houver ALERTA, sem bloquear nada). Imagens e bancos não são verificados. Uso manual: `py .kiro/scripts/verificar_publicacao.py --git`; para ignorar uma linha, `verificar-publicacao: ignorar`.

## Validação (29/10/2026)

- Os dois scripts compilam; formatos conferidos contra a documentação; `name` da skill igual ao nome da pasta.
- `verificar_publicacao.py --autoteste`: 12 verificações aprovadas, em pasta temporária, sem alterar arquivo.
- Hook simulado com eventos JSON sintéticos: arquivo com valor falso gerou ALERTA e saída 1, arquivo limpo saída 0.
- `--git` no repositório: 0 alertas; os avisos são `mesa_certa.db` e as imagens, que exigem conferência manual.
- `inspecionar_workflow.py` rodado sobre os três workflows, sem executar nada.

## Limitações

- O Kiro informa que os hooks valem a partir da próxima sessão. O **disparo automático real não foi observado**, só simulado, e os gatilhos de arquivo valem para alterações do agente, não para edição manual.
- A skill ainda não foi ativada pelo Kiro em uma conversa; foram validados o formato e o script.
- A checagem é por padrões e pelos valores do `.env` e do `crm-mock.py`: pode dar falso positivo e não cobre todo tipo de segredo nem imagens.
- O comando usa o launcher `py` do Windows; em outro sistema, troque por `python3`.
