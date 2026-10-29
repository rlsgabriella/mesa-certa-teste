# Workflows n8n

Esta pasta tem os exports **finais** dos workflows, lidos da instância n8n em
29/10/2026. Os JSON contêm só referências a credenciais (nome e id), sem valores.

| Arquivo | Versão exportada | Situação |
|---|---|---|
| `wf01-recebimento-cadastro-leads.json` | id `bZu7Ku16BbgSj504`, `versionId 3c85f463-…`, 18 nós | Recebe o webhook, valida HMAC, classifica, persiste (`pedidos_formulario` + `sync_eventos`), responde 200/401 e cria no CRM só se comercial. **Aprovado** no T1.005 (execução 355, success). |
| `wf02-conciliacao-marketing-crm.json` | id `fcMKsKzpcdAMKnr0`, `versionId 63d1f2b0-…`, 12 nós | Busca pendentes comerciais, consulta o CRM por e-mail antes de criar, atualiza `sync_eventos` para `sincronizado`. **Aprovado** na execução 356 (success). |
| `wf03-resumo-semanal.json` | importado como `wrGCERjaPYAeDcuH`, 11 nós | Resumo semanal da gestora: Schedule Trigger `0 8 * * 1` → serviço local de indicadores → resumo → e-mail (só com destinatário) ou registro; falhas ficam registradas. **Execuções manuais 357 e 359 com sucesso (e-mail aceito pelo SMTP); agendamento não observado.** A cópia importada **não tem o fuso `America/Sao_Paulo`** que este arquivo traz em `settings`: sem ele, o n8n usa o fuso da instância (`America/New_York`, visto na execução 360). Ver `../scripts/README.md`. |

**Observação sobre o WF01 exportado:** a execução 355 rodou na versão `88e7d88f-…` (22 nós).
Logo depois, os 4 nós SQLite antigos (`CUSTOM.sqliteNode`), que estavam desconectados,
foram removidos no editor (versão exportada, 18 nós). Comparação feita entre as duas
versões: só essas 4 remoções; nenhum nó, parâmetro ou conexão do caminho executado mudou.
A versão de 18 nós em si não foi executada.

Versões anteriores, backups e as cópias de importação ficam na pasta de
desenvolvimento fora do pacote (`mesa-certa-teste-dev/workflows/`).

Resultado comprovado das execuções: `../evidencias/02-workflow-01/t1-005-aprovado.md` (355) e
`../evidencias/03-workflow-02/wf02-execucao-356.md` (356). Índice completo: `../evidencias/README.md`.

Antes de exportar qualquer workflow, confira `../configuracoes/README.md`:
o JSON exportado não pode conter o segredo do HMAC nem o token do CRM.

### Histórico das correções de 29/10/2026 (resumo; os JSON de cada etapa estão na pasta de desenvolvimento)

> Esta seção descreve as correções feitas antes do export final. Itens que dizem
> `CUSTOM.sqliteNode` ou `ja_no_crm` foram **superados**: os exports finais usam
> `n8n-nodes-sqlite3.sqliteNode` e o WF02 grava `sincronizado`.

Workflow 01:
- Campo `"=nome"` do POST ao CRM corrigido para `"nome"` (o `=` sobrando
  enviava a chave errada ao `POST /deals`).
- Removido o `pinData` de teste (`teste-suporte-real-005`) que congelava a
  entrada do nó "Preparar Dados do Lead".
- Confirmado (já estava correto no editor): `Classificar Pedido` executa antes
  do INSERT; o INSERT em `pedidos_formulario` persiste a coluna `classificacao`.

Workflow 02:
- Removido o `event_id` fixo de teste (`'teste-hmac-valido-001'`) do nó
  "Vincular Negócio Existente".
- "Vincular Negócio Existente": trocado de `SELECT` para `UPDATE`, marcando
  `estado_sync='ja_no_crm'` com o `deal_id` do GET e o `event_id` do pendente.
- Padronizados os nós SQLite para `CUSTOM.sqliteNode` (antes havia
  `n8n-nodes-sqlite3.sqliteNode` misturado) e os parâmetros para formato de array.
- Completados os dois caminhos do IF "Negócio criado após erro?": novo nó
  "Confirmar Sincronização após Erro" (ramo verdadeiro → `sincronizado`) e
  "Marcar Falha de Sincronização" (ramo falso → `falha`, incrementa `tentativas`).
- Corrigido o parâmetro de e-mail do GET inicial (tinha espaço: `"= {{...}}"`).

Importação sem sobrescrever o que está rodando: ver a seção ao final deste arquivo.

---

## Regras de negócio a implementar

Estas regras vieram da implementação Python antiga (arquivada fora do
repositório, ver `../../log-de-decisoes.md`) e da documentação do desafio.
Cada regra indica a origem e se já foi verificada.

### Fontes de dados e fusos

| Fonte | Campo de data | Fuso |
|---|---|---|
| Webhook do marketing (`criado_em`) | `2026-10-05T03:42:18Z` | UTC |
| `pedidos_formulario.criado_em` | idem | UTC |
| `negocios_crm.criado_em`, `atualizado_em`, `primeiro_contato_em` | `2026-10-05 00:42:18` | Brasília (UTC-3) |
| `historico_etapas.em` | idem | Brasília |

"Semana passada" = 05/10 00:00:00 a 11/10 23:59:59 em Brasília,
ou seja, `2026-10-05T03:00:00Z` a `2026-10-12T02:59:59Z` no webhook.
"Agora" no desafio = segunda 12/10/2026 08:00 Brasília.

### R1. Validação HMAC (workflow 01)

- Cabeçalho `X-Signature` = `sha256=` + HMAC-SHA256 do **corpo bruto**, em hexadecimal.
- Calcular sobre os bytes recebidos, nunca sobre `JSON.stringify($json.body)`:
  o n8n reserializa o corpo e os acentos mudam, e a assinatura deixa de bater.
- No n8n: nó Webhook com a opção **Raw Body** ligada; no Code node,
  `await this.helpers.getBinaryDataBuffer(0, 'data')`.
- Comparar em tempo constante (`crypto.timingSafeEqual`), checando antes se os
  dois valores têm o mesmo tamanho (senão a função lança erro).
- O segredo vem de credencial ou variável de ambiente, nunca do código.
- Verificado: para `evt_500110`, o HMAC do corpo bruto confere com o cabeçalho.
- Dado do lote: 3 entregas têm assinatura inválida (`evt_500188`, `evt_500200`,
  `evt_500244`). Esses eventos não podem entrar em nenhuma contagem nem no CRM.

### R2. Resposta ao remetente (workflow 01)

Regras do remetente (`webhook/README.md`): 2xx = recebido; 5xx, erro de conexão
ou mais de 5 s = reenvia (até 4 tentativas); 4xx = não reenvia.

| Situação | Resposta | Origem |
|---|---|---|
| Assinatura inválida | 401 | Python antigo |
| Corpo não é JSON | 400 | Python antigo. O lote tem 2 linhas com JSON quebrado. |
| Falta `event_id`, `criado_em`, `nome`, `email` ou `telefone` | 400 | Python antigo |
| `event_id` já recebido | 200 (não reprocessa) | Python antigo |
| Evento novo | 200 depois de guardar o evento | Python antigo |

Ponto de projeto ainda aberto: o CRM mock às vezes demora 8 s. Se o workflow só
responder ao remetente depois de chamar o CRM, a resposta passa de 5 s e o
remetente reenvia. O Python resolvia isso respondendo logo após guardar o evento
e sincronizando com o CRM depois. No n8n isso pede um nó "Respond to Webhook"
antes das chamadas ao CRM e um lugar para guardar os eventos pendentes.

### R3. Eventos duplicados (workflows 01 e 02)

- **Reenvio do mesmo evento:** mesmo `event_id`. Processar uma única vez.
  Na semana houve 14 `event_id` entregues mais de uma vez.
- **Mesma pessoa, eventos diferentes:** `event_id` diferentes com o mesmo e-mail
  normalizado (exemplo: `evt_500113` e `evt_500114`, o segundo com espaço no fim
  do e-mail). Antes de criar, consultar `GET /deals?email=` e não criar outro negócio.
- **E-mail e telefone apontando para negócios diferentes:** não vincular
  automaticamente, mandar para revisão. Ocorreu em 2 eventos da semana.

### R4. Normalização (workflows 01 e 02)

- E-mail: `trim` + minúsculas.
- Telefone: só dígitos; se tiver 12 dígitos ou mais e começar com `55`, remover o `55`.
- Nomes com acento quebrado (`JoÃ£o`) aparecem em 12 eventos do lote. Não
  corrigir o texto; a identificação usa e-mail e telefone.

### R5. Classificação (workflows 01 e 02)

Nada é apagado: a classificação só decide se o pedido vira negócio no CRM ou vai
para revisão. Categorias necessárias:

| Categoria | Exemplos reais do lote |
|---|---|
| Comercial (pedido de demonstração) | "Quero uma demonstração do cardápio digital...", "Quanto custa?", "Podem me ligar?" |
| Suporte (já é cliente) | "Esqueci minha senha de acesso ao painel", "A impressora não está imprimindo os pedidos desde ontem", "Meu acesso foi bloqueado, já sou cliente de vocês há 2 anos" |
| Fornecedor (quer vender para a Mesa Certa) | "Somos uma fornecedora de embalagens...", "Agência de marketing digital...", "...empresa de maquininhas de cartão..." |
| Teste interno | nome "Fulano de Tal" / "asdf", e-mail `@mesacerta.com.br` ou `teste@teste.com`, mensagem "testando o formulário" |
| Spam | "Compre seguidores baratos!...", "Ganhe dinheiro rápido clicando aqui http://bit.ly/..." |

Defeitos da regra antiga que **não** devem ser copiados:
- O marcador `test` também pega "Quero **test**ar o sistema de vocês. Como começo?".
  Isso marcou 5 pedidos comerciais da semana como teste
  (`evt_500177`, `evt_500183`, `evt_500184`, `evt_500185`, `evt_500198`).
- Não havia categoria de suporte nem de fornecedor.
- Mensagens vazias, ".", "???" ou "123" não provam que é teste. Decidir pelo
  conjunto (nome, e-mail, restaurante), não só pela mensagem.

### R6. Erros do CRM (workflow 01)

Comportamento do CRM mock (`crm-mock-teste/crm-mock.py`):

| Resposta | Frequência no mock | Tratamento |
|---|---|---|
| 201 `deal_id` | normal | Criado. |
| 409 `email_ja_cadastrado` | e-mail já existe (compara com `trim` + minúsculas) | Sucesso: usar o `deal_id` devolvido. |
| 422 / 400 | campo faltando / JSON inválido | Erro do nosso lado: não repetir, registrar. |
| 401 | sem `Authorization: Bearer ...` | Erro de configuração. |
| 429 + `Retry-After: 1` | mais de 5 requisições por segundo | Esperar o `Retry-After` e repetir. |
| 500 | 10% das chamadas | Repetir com espera crescente. **No POST, metade desses 500 grava o negócio mesmo assim**: antes de repetir o POST, consultar `GET /deals?email=`. |
| 200 com `"status": "erro"` | 8% das chamadas | Não é sucesso: repetir. |
| Atraso de 8 s | 6% das chamadas | Timeout do nó HTTP acima de 8 s. |

Esperas usadas no Python: 0,5 s, 1 s, 2 s e 4 s (até 5 tentativas).

### R7. Conciliação marketing × CRM (workflow 02)

Ordem das categorias, uma por evento: inválido > teste > spam > legítimo.
Para cada evento legítimo da semana, procurar negócio no CRM por e-mail **ou**
telefone normalizados e separar em:
- vinculado a negócio criado na semana;
- vinculado só a negócio antigo;
- sem correspondência (candidato a recuperação, primeiro em modo dry-run).

A regra de cruzamento muda o resultado: só por e-mail dá 21 sem correspondência;
por e-mail ou telefone dá 19 (`evt_500148` e `evt_500190` só batem pelo telefone).
Ver `../evidencias/01-auditoria/auditoria-2026-10-28.md`.

### R8. Indicadores comerciais (workflows 03 e 04)

- **Negócios por etapa:** contagem de `negocios_crm.etapa` (ou `GET /estado` no CRM).
  Etapas: Novo, Contato, Reunião marcada, Reunião realizada, Perdido.
- **Pedidos da semana:** contar pela data de **criação** (`criado_em`).
  A planilha da gestora (187) bate dia a dia com a data da **última atualização**
  (`atualizado_em`), que inclui negócios antigos alterados na semana.
- **Prazo de primeiro contato (SLA):** 4 horas úteis, segunda a sexta, 08:00–18:00
  Brasília, contadas de `criado_em` até `primeiro_contato_em`. Feriados não
  descontados (suposição registrada em `suposicoes.md`).
- **SDR:** campo `responsavel` (`sdr_1`, `sdr_2`, `sdr_3`).
  Limitação: `atualizado_por` costuma ser outro SDR, e o banco não registra
  quem fez o primeiro contato.
- **Sem retorno agora:** negócio sem `primeiro_contato_em`, que não seja teste,
  suporte, fornecedor ou spam, com prazo vencido em 12/10 08:00.
- **Negócios fechados sem contato:** 20 negócios estão em Perdido sem
  `primeiro_contato_em`; 7 deles foram movidos pela `automacao_limpeza`.
  Devem aparecer no indicador, não sumir dele.

Nenhum cálculo de SLA ou de resumo semanal existia no Python: os workflows 03 e
04 começam do zero.


---

## Como importar os exports finais sem sobrescrever o que está rodando

Os exports mantêm o `id` da instância onde foram gerados (`bZu7Ku16BbgSj504` no WF01,
`fcMKsKzpcdAMKnr0` no WF02). Importe como workflow novo. Para revisar antes de adotar:

1. No n8n, crie um workflow novo (não abra o que está em uso).
2. Menu → **Import from File** e escolha o JSON desta pasta.
3. O workflow entra como uma cópia nova (o n8n gera outro id interno ao criar
   via tela). Revise nó a nó e rode os testes.
4. Só depois de validar, substitua o workflow antigo (ou renomeie o antigo
   para `... (antigo)` e ative a cópia revisada).
5. Reassocie as credenciais se o n8n pedir: **Header Auth** (CRM) e
   **SQLite Database account**. Os ids de credencial no JSON
   (`rmoFJ2XC21kBrCVT`, `A6Zo3HG9VmdtVFOr`) só resolvem na instância onde foram
   criados; em outra instância, selecione as credenciais equivalentes na mão.

Pré-requisitos de ambiente (iguais aos atuais):
- Variáveis `MESA_CERTA_HMAC_SECRET`, `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` e
  `NODE_FUNCTION_ALLOW_BUILTIN=crypto` definidas no processo do n8n
  (ver `../configuracoes/README.md`).
- CRM mock no ar em `http://127.0.0.1:8001`.
- Pacote comunitário `n8n-nodes-sqlite3` instalado (os workflows usam
  `n8n-nodes-sqlite3.sqliteNode`).

> Nota: foram executados e aprovados o T1.005 do WF01 (execução 355) e a conciliação
> do WF02 (execução 356). **Ainda sem execução**: suporte/não comercial, reenvio do
> mesmo `event_id`, assinatura inválida (HTTP 401), o ramo em que o WF02 cria o
> negócio por POST, falhas 429/500 do CRM e o lote completo.
