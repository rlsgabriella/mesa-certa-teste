# Evidências: índice para o avaliador

Uma subpasta por tema; caminhos relativos a esta pasta. Horários em Brasília, salvo indicação de UTC. Formato das provas: relatórios em Markdown, resultados em JSON, estado final do CRM e duas capturas do teste agendado do WF03. Prints antigos do WF01 e do e-mail das 14:53 foram retirados por conter dados que não serão publicados; não eram obrigatórios.

## Em uma tela

| Workflow | Comprovado | **Não** comprovado |
|---|---|---|
| **01** Recebimento | Lead **comercial** com HMAC válido: HTTP 200, classe `comercial`, gravado no SQLite e negócio 20395 no CRM (execução **355**, 29/10). | Suporte/não comercial, reenvio do mesmo `event_id`, assinatura inválida (401), falhas 429/500 e lote completo. A versão exportada (18 nós) não foi executada; a 355 rodou na de 22 nós. |
| **02** Conciliação | Execução **356**: localizou o negócio 20395 pelo e-mail e marcou o evento 005 como `sincronizado`, sem duplicar o CRM. | Ramo de criação por POST, tratamento de erro do CRM e vários eventos. |
| **03** Resumo semanal | Cálculo reproduz a apuração de 12/10/2026 08:00 (23 de 23) com 25 testes. Execução **361**, agendada, 29/10 às 16:50: e-mail aceito e recebido. | A **segunda 08:00** (o teste usou cron diário). Dados **desatualizados**: a cópia do CRM no SQLite termina em 11/10, então o resumo saiu com 0 negócios e avisa isso. |

## Arquivos

```
01-auditoria/       auditoria-2026-10-28.md
02-workflow-01/     t1-005-aprovado.md · t1-005-resultado.json · crm-estado-teste-joao-almeida-20392.json
03-workflow-02/     wf02-execucao-356.md · wf02-execucao-356.json
04-workflow-03/     validacao-resumo-semanal-2026-10-12.md · resumo-semanal-2026-10-12.json/.txt
                    wf03-execucao-361-agendada.md · execucao-automatica.png · email-chega.png
                    Mesa Certa_03-Resumo Semanal da Gestora.json
05-testes-banco/    registros-de-teste-banco.md
```

| Arquivo | O que prova | Limites |
|---|---|---|
| `01-auditoria/auditoria-2026-10-28.md` | Integridade dos bancos e do repositório e números do lote (28/10, só leitura). | Anterior às correções; usa a regra antiga de classificação. |
| `02-workflow-01/t1-005-*` | Teste T1.005, nó a nó, com SQLite e CRM antes e depois: `pedidos_formulario` id 105, `sync_eventos` `pendente`, CRM 394 para 395. | Um único evento comercial. `sync_eventos` fica `pendente` (quem atualiza é o WF02). |
| `02-workflow-01/crm-estado-teste-joao-almeida-20392.json` | Estado do CRM após o teste de 28/10 (negócio 20392). | Versão anterior do WF01; 391 dos 392 negócios são fictícios do desafio. Não prova reenvio. |
| `03-workflow-02/wf02-execucao-356.*` | Execução 356 (`fcMKsKzpcdAMKnr0`, 13:17): `sync_eventos` de `pendente` para `sincronizado` com `deal_id` 20395; CRM continua com 395. | Só o ramo "negócio já existe". |
| `04-workflow-03/validacao-…md`, `resumo-…json/.txt` | 23 de 23 indicadores conferem; original e cópia com o mesmo SHA-256. | Valida o **cálculo**, não o workflow. Classificação por texto, sem revisão humana. Mediana 2,08 h úteis contra 2,15 na apuração antiga. |
| `04-workflow-03/wf03-execucao-361-agendada.md` | Relato da execução 361 lido no n8n: modo `trigger`, 16:50:00 em `America/Sao_Paulo`, "Enviar e-mail" aceito pelo SMTP. | Cron diário de teste; destinatário não registrado. |
| `04-workflow-03/Mesa Certa_03-Resumo Semanal da Gestora.json` | Export do WF03 como está no n8n depois do teste: 11 nós, `timezone` `America/Sao_Paulo`, cron `0 0 8 * * 1`, workflow **inativo**. Só traz a referência à credencial SMTP, sem e-mail nem segredo. | Estado do export, não prova de execução. A cópia de referência é `solucao/workflows/wf03-resumo-semanal.json`. |
| `04-workflow-03/execucao-automatica.png` | Tela de Executions: #361, 29/10 16:50:00, `Succeeded in 3.702s`, sem o ícone de teste manual das execuções 357 a 360. | A imagem não escreve o modo (está no relato). Mostra "Publish": workflow inativo na captura. |
| `04-workflow-03/email-chega.png` | E-mail do resumo recebido às 16:50 ("posição em 29/10 às 16:50"). | Corpo cortado; resumo com 0 negócios e aviso de CRM desatualizado. Veja Segurança. |
| `05-testes-banco/registros-de-teste-banco.md` | O que `mesa_certa.db` tem a mais que o original (tabela `sync_eventos`, ids 101 a 105, negócios 20392 a 20395) e como voltar ao início. | Original intacto (SHA-256 `F545271F…40D6`). |

O e-mail das 14:53 (execução manual 357) foi confirmado pela autora; sem arquivo, é declaração dela e não prova agendamento.

## Segurança e dados pessoais

Verificação de 29/10/2026. Nenhum valor secreto é reproduzido aqui.

| Item | Situação |
|---|---|
| Segredo HMAC e token do CRM | Não aparecem em nenhum arquivo desta pasta nem no histórico do `main`. |
| `email-chega.png` | Tarja sobre o nome do endereço; **a miniatura da foto de perfil e o `@gmail.com` seguem visíveis**, por decisão da autora. |
| Nomes, e-mails e telefones | Dos JSON e do texto: conjunto fictício do desafio. Exceção: `t1.comercial.005@teste-mesacerta.example`, criado nos testes. |

## Reprodução

```powershell
py -m unittest solucao/scripts/test_resumo_semanal.py -v                  # 25 testes
$env:MESA_CERTA_HMAC_SECRET = "<segredo do desafio>"                       # só para conferir as assinaturas do lote
py solucao\scripts\validar_resumo_historico.py --saida-dir solucao\evidencias\04-workflow-03
```
