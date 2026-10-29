# Pacote do assistente de IA (Kiro)

Exigência do enunciado (item 6): instruções fixas, procedimento reutilizável e checagem automática, mais [`quando-usar-o-que.md`](../quando-usar-o-que.md).
Os três componentes usam os formatos e as pastas do Kiro (conferidos na documentação oficial em kiro.dev: *Steering*, *Agent Skills* e *Hooks*). Pasta usada: `.kiro/` na raiz do projeto, versionada com o repositório.

| Componente | Caminho | Formato Kiro | Quando é usado |
|---|---|---|---|
| Instruções persistentes | [`steering/mesa-certa-projeto.md`](steering/mesa-certa-projeto.md) | Steering com `inclusion: always` | Lido em toda conversa neste projeto |
| Skill de auditoria | [`skills/auditoria-workflow-crm/`](skills/auditoria-workflow-crm/SKILL.md) | Agent Skill (`SKILL.md` com `name` e `description`, `references/`, `scripts/`) | Automática quando o pedido combina com a descrição, ou manual com `/auditoria-workflow-crm` |
| Hooks de publicação | [`hooks/verificar-segredos-ao-salvar.json`](hooks/verificar-segredos-ao-salvar.json) e [`hooks/verificar-segredos-ao-criar.json`](hooks/verificar-segredos-ao-criar.json) | Hook `v1`, ação `command`, gatilhos `PostFileSave` e `PostFileCreate` | Quando o agente salva ou cria um arquivo de texto |

Script do hook: [`scripts/verificar_publicacao.py`](scripts/verificar_publicacao.py). Script da skill: [`skills/auditoria-workflow-crm/scripts/inspecionar_workflow.py`](skills/auditoria-workflow-crm/scripts/inspecionar_workflow.py).

## 1. Instruções persistentes

Sete blocos: segurança (nunca imprimir valores de segredo), preservação de dados (`mesa_certa.original.db` imutável, nada de commit ou push sem pedido), qualidade das evidências (só o que foi executado e conferido),
validação de indicadores (data de referência como parâmetro e a base histórica de 12/10/2026), limitações que sempre se documentam, separação entre sugestão da IA e decisão humana, e as ferramentas do projeto.
Quando o arquivo foi criado, o Kiro passou a injetá-lo nas mensagens seguintes como regra do workspace, o que confirma o carregamento.
Alternativa suportada, não usada: `AGENTS.md` na raiz.

## 2. Skill `auditoria-workflow-crm`

Etapas: inspeção, entradas, saídas, idempotência, tratamento de erros, evidências, segurança e relatório final.
Material de apoio: [`references/checklist.md`](skills/auditoria-workflow-crm/references/checklist.md) e [`references/modelo-relatorio.md`](skills/auditoria-workflow-crm/references/modelo-relatorio.md).
O script `inspecionar_workflow.py` lê um JSON exportado do n8n, sem executar nada, e informa gatilhos, credenciais por referência, `pinData`, nós soltos, saídas de erro sem destino, resposta ao remetente, SQL com ou sem proteção contra duplicidade, referências a nós inexistentes e sinais de segredo.

Como usar:

```
/auditoria-workflow-crm Audite solucao/workflows/wf01-recebimento-cadastro-leads.json e diga quais caminhos a execução 355 comprova.
py .kiro/skills/auditoria-workflow-crm/scripts/inspecionar_workflow.py solucao/workflows/wf01-recebimento-cadastro-leads.json
```

Resultado real sobre o WF01 exportado (nenhuma execução foi feita): 0 alertas e 2 avisos, a saber, o nó "Criar Negócio no CRM" sem retry e o Code node que registra saída junto de variável de ambiente (o hash do segredo no log).
Informou também que a resposta 200 sai antes das chamadas ao CRM, que os dois `INSERT` são idempotentes e que o webhook usa o corpo bruto. No WF02 avisa que o gatilho é manual.

## 3. Hooks de publicação

Cada hook chama `py .kiro/scripts/verificar_publicacao.py --stdin` (timeout de 20 s). O script:

- **só lê:** abre arquivos para leitura e executa apenas `git status --porcelain` e `git check-ignore`; não grava, move nem apaga;
- **nunca imprime valores:** mostra arquivo, linha e o tipo (valor de variável do `.env`, token de teste do `crm-mock.py`, Bearer, JWT, chave privada, atribuição de segredo, `.env` não ignorado pelo git, arquivo de credencial);
- **avisa, não bloqueia:** sai com 1 se houver ALERTA; os gatilhos `PostFile*` não bloqueiam nada;
- avisa que imagens e bancos (`.png`, `.db`) não são verificados e merecem conferência manual;
- aceita `--git` (arquivos modificados ou novos), caminhos explícitos e `--autoteste`.

Uso à mão: `py .kiro/scripts/verificar_publicacao.py --git`. Para ignorar uma linha de propósito, ponha `verificar-publicacao: ignorar` nela.

## 4. Validação feita (29/10/2026)

- Os JSON dos hooks e o formato do `SKILL.md` e do steering foram conferidos contra a documentação; `name` da skill igual ao nome da pasta; os dois scripts compilam.
- `verificar_publicacao.py --autoteste`: 12 verificações aprovadas, em pasta temporária (texto limpo sem alerta; Bearer, JWT, chave e valor do `.env` com alerta; linha marcada ignorada; imagem só com aviso; nenhum arquivo alterado).
- Simulação do hook com eventos JSON sintéticos: arquivo com valor falso gerou ALERTA e saída 1, arquivo limpo saída 0, e os hashes dos arquivos não mudaram. O nome do campo com o caminho no evento não está documentado, então o script procura qualquer valor que aponte para um arquivo existente.
- `--git` sobre o repositório: 42 arquivos, 0 alertas, 2 avisos (`mesa_certa.db` e `email-evidencia.png`, binários não verificáveis; o print foi retirado depois dessa varredura).
- `inspecionar_workflow.py` rodado sobre os três JSON de `solucao/workflows/`, sem executar nada.

## 5. Limitações

- O Kiro informa que os hooks entram em vigor **na próxima sessão**; o disparo automático por evento ainda não foi observado, só a simulação. Os gatilhos de arquivo valem para alterações feitas pelo agente, não pela edição manual.
- A skill ainda não foi ativada pelo Kiro em uma conversa: foram validados o formato e o script de apoio.
- A checagem de segredos é por padrões e pelos valores do `.env` e do `crm-mock.py`: pode ter falso positivo e não cobre todo tipo de segredo nem o conteúdo de imagens.
- O comando usa o launcher `py` do Windows; em outro sistema, troque por `python3`.
- Os hooks avisam; quem decide o que fazer com um alerta é a pessoa.
