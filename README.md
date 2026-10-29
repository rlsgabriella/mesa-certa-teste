# Teste técnico Mesa Certa

## 1. O que a solução faz

Recebe os pedidos do formulário e entrega à gestora comercial os números que ela pediu, com n8n, SQLite e Python (Python só para o CRM mock, o remetente do desafio e o cálculo dos indicadores).

```
Formulário --POST--> WF01 --> SQLite (pedidos_formulario, sync_eventos) --> CRM mock (:8001)
                                                                             ^
                          WF02 (gatilho manual) localiza o negócio e marca o pedido 'sincronizado'
SQLite --leitura--> resumo_semanal.py --JSON/texto--> WF03 (segunda 08:00) --> e-mail
```

| Workflow | Função | Arquivo |
|---|---|---|
| **01** Recebimento | Valida a assinatura, classifica, grava, responde 200 e cria o negócio só para pedido comercial. | [`wf01-…json`](solucao/workflows/wf01-recebimento-cadastro-leads.json) |
| **02** Conciliação | Localiza o negócio pelo e-mail e marca `sincronizado`; cria o negócio se faltar. | [`wf02-…json`](solucao/workflows/wf02-conciliacao-marketing-crm.json) |
| **03** Resumo semanal | Chama o cálculo (serviço local, somente leitura) e envia o resumo por e-mail. | [`wf03-…json`](solucao/workflows/wf03-resumo-semanal.json) |

Como instalar, configurar e rodar: [`como-assumir.md`](como-assumir.md). Números da gestora: [`respostas.md`](respostas.md).

## 2. Resultados comprovados

| Item | Resultado | Evidência |
|---|---|---|
| WF01, execução **355** | Lead comercial com assinatura válida: HTTP 200, classe `comercial`, pedido 105 no SQLite, negócio **20395** criado (CRM de 394 para 395). | [relato](solucao/evidencias/02-workflow-01/t1-005-aprovado.md) |
| WF02, execução **356** | Localizou o negócio 20395 já existente e marcou o pedido 005 como `sincronizado`, sem duplicar (CRM continua com 395). | [relato](solucao/evidencias/03-workflow-02/wf02-execucao-356.md) |
| WF03, cálculo | Referência 12/10/2026 08:00: **23 indicadores** conferem com a apuração (funil 391, 187 atualizados, 142 criados, 136 pedidos comerciais, 12 sem correspondência, 68 sem retorno vencido). 25 testes automatizados passam. | [validação](solucao/evidencias/04-workflow-03/validacao-resumo-semanal-2026-10-12.md) |
| WF03, envio | Execução **361**, disparada pelo Schedule Trigger em 29/10 às 16:50 (modo `trigger`): e-mail aceito pelo SMTP e recebido no mesmo minuto. Execuções 357 e 359 foram manuais. | [relato](solucao/evidencias/04-workflow-03/wf03-execucao-361-agendada.md), [execução](solucao/evidencias/04-workflow-03/execucao-automatica.png), [e-mail](solucao/evidencias/04-workflow-03/email-chega.png) |

Índice completo das provas e limitações: [`solucao/evidencias/README.md`](solucao/evidencias/README.md).

## 3. Estrutura

```
README.md · problemas.md · respostas.md · suposicoes.md · como-assumir.md · guia-para-ela.md · quando-usar-o-que.md · log-de-decisoes.md · enunciado.md
mesa_certa.original.db (intacto) · mesa_certa.db (trabalho, com registros de teste)
solucao/  workflows/ (3 exports) · scripts/ · configuracoes/ (.env.example) · crm-mock-teste/ · evidencias/ · testar_webhook_hmac.py
webhook/  remetente e lote do marketing (segredo trocado por placeholder)
.kiro/    pacote do assistente: steering/ · skills/auditoria-workflow-crm/ · hooks/ · scripts/
```

Fora do pacote: `../mesa-certa-teste-dev/` (backups, versões intermediárias e os READMEs removidos; não enviar).

## 4. Limitações

- Cada workflow tem **um caminho** comprovado. Sem execução: suporte, reenvio do mesmo pedido, assinatura inválida (401), falhas 429/500 do CRM, criação de negócio pelo WF02 e lote completo. O WF01 exportado (18 nós) não foi executado; a 355 rodou antes da remoção de 4 nós soltos.
- **WF03:** o disparo agendado foi visto uma vez, com um cron diário de teste. **A segunda às 08:00 não foi observada.** No n8n o workflow ficou inativo e com o cron de teste. A primeira tentativa (16:20) não disparou porque a cópia importada não tinha o fuso `America/Sao_Paulo`.
- **A cópia SQLite do CRM está desatualizada** (último registro em 11/10). O e-mail de teste saiu com 0 negócios na semana e o aviso correspondente; não serve como visão atual da operação.
- A classificação de pedidos é uma regra por texto, sem revisão humana. O banco não registra quem fez cada contato, então o prazo por SDR não prova atraso individual.
- Pacote Kiro: o disparo automático dos hooks e o uso da skill em conversa ainda não foram observados (só simulados).

## 5. Segurança

- `.env` é ignorado pelo git. O WF01 grava o hash do segredo no log do n8n.
- **O repositório é público.** O segredo HMAC de teste e os 3 prints do WF01 estavam no commit `2c3ef90`. O histórico foi reescrito e publicado em 29/10 (`origin/main` a partir de `6227691`) e conferido depois do `fetch`: o segredo não aparece no histórico nem na árvore. O commit antigo pode seguir acessível pelo hash, então **trate o segredo como exposto e peça a troca a quem o forneceu**.
- O token de teste do CRM continua em `solucao/crm-mock-teste/crm-mock.py` (arquivo do desafio, necessário para o mock autenticar).
- `email-chega.png` tem tarja sobre o nome do endereço; a miniatura da foto de perfil e o `@gmail.com` ficam visíveis, por decisão da autora. O print original sem tarja não está no repositório.
- Antes de publicar: `py .kiro/scripts/verificar_publicacao.py --git`.