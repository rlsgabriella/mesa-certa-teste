# Evidências: índice para o avaliador

Cada comprovação está em uma subpasta por tema. Os caminhos abaixo são relativos a esta pasta.
Horários em Brasília (UTC-3), salvo indicação de UTC. Os arquivos foram só movidos para estas subpastas (SHA-256 igual antes e depois da mudança).
A única edição posterior foi o ajuste de referências de caminho em `01-auditoria/auditoria-2026-10-28.md` (duas) e em
`05-testes-banco/registros-de-teste-banco.md` (uma).

**Formato das provas:** relatórios em Markdown, resultados em JSON e o estado final do CRM. Três prints do WF01 (`get.png`, `post.png` e
`lead.png`) foram retirados do pacote por decisão da autora, por conterem informações que não serão publicadas; não eram obrigatórios, porque
as execuções e os resultados no CRM já estão documentados nos arquivos de texto. O print do e-mail do WF03 (`email-evidencia.png`) também foi
retirado por decisão da autora, por mostrar endereço de e-mail e foto de perfil reais; o recebimento fica registrado só em texto.

## Em uma tela

| Workflow | O que está comprovado | O que **não** está comprovado | Onde ver |
|---|---|---|---|
| **01** Recebimento de leads | Um lead **comercial** com HMAC válido foi aceito (HTTP 200), classificado como `comercial`, gravado no SQLite e virou o negócio 20395 no CRM (execução **355**, `success`, 29/10). | Lead de suporte/não comercial, reenvio do mesmo `event_id`, assinatura inválida (HTTP 401), falhas 429/500 do CRM e o lote completo não foram executados. A versão exportada (18 nós) não foi executada: a 355 rodou na versão de 22 nós. | [02-workflow-01](02-workflow-01/) |
| **02** Conciliação | A execução **356** (`success`, 29/10) **localizou um negócio já existente** (20395) pelo e-mail e marcou o evento 005 como `sincronizado`, sem duplicar o CRM. | O ramo em que o WF02 **cria** o negócio por POST, o tratamento de erro do CRM e a conciliação de vários eventos não foram exercitados. | [03-workflow-02](03-workflow-02/) |
| **03** Resumo semanal | O **cálculo** reproduz a apuração histórica de 12/10/2026 08:00 (23 de 23 números), com 25 testes automatizados aprovados. Um **e-mail de teste manual** com o resumo foi recebido em 29/10 às 14:53. | O **agendamento automático** (segunda 08:00) nunca foi observado. O e-mail de teste mostra dados **desatualizados**: a cópia do CRM no SQLite termina em 11/10, então o resumo saiu com 0 negócios na semana e avisa disso. | [04-workflow-03](04-workflow-03/) |

## Mapa de arquivos

```
evidencias/
├─ README.md                                  este índice
├─ 01-auditoria/
│  └─ auditoria-2026-10-28.md
├─ 02-workflow-01/
│  ├─ t1-005-aprovado.md · t1-005-resultado.json
│  └─ crm-estado-teste-joao-almeida-20392.json
├─ 03-workflow-02/
│  └─ wf02-execucao-356.md · wf02-execucao-356.json
├─ 04-workflow-03/
│  ├─ validacao-resumo-semanal-2026-10-12.md
│  └─ resumo-semanal-2026-10-12.json · resumo-semanal-2026-10-12.txt
└─ 05-testes-banco/
   └─ registros-de-teste-banco.md
```

## 01-auditoria

| Arquivo | Descrição | Resultado | Limitações |
|---|---|---|---|
| [auditoria-2026-10-28.md](01-auditoria/auditoria-2026-10-28.md) | Integridade dos bancos e do repositório, números do lote e do CRM (28/10, só leitura). | Bancos do desafio idênticos aos originais; números confirmados separados das hipóteses. | Anterior às correções e aos testes de 29/10. Os números de classificação usam a regra antiga, depois refinada (ver [04-workflow-03](04-workflow-03/)). Menciona scripts arquivados fora do repositório. |

## 02-workflow-01

| Arquivo | Descrição | Resultado | Limitações |
|---|---|---|---|
| [t1-005-aprovado.md](02-workflow-01/t1-005-aprovado.md) | Relato nó a nó do teste T1.005: envio, execução 355, SQLite e CRM, antes e depois. | **Aprovado**: HTTP 200, `assinatura_valida: true`, classe `comercial`, `pedidos_formulario` id 105, `sync_eventos` `pendente`, CRM 394 para 395, negócio 20395 na etapa Novo. | Um único evento comercial. `sync_eventos` ficou `pendente` (o WF01 não o atualiza; isso é feito pelo WF02). Não cobre os demais cenários. |
| [t1-005-resultado.json](02-workflow-01/t1-005-resultado.json) | Os mesmos resultados em formato estruturado. | Idêntico ao relato. | Mesmas limitações. |
| [crm-estado-teste-joao-almeida-20392.json](02-workflow-01/crm-estado-teste-joao-almeida-20392.json) | Estado do CRM mock depois do primeiro teste de 28/10 (392 negócios). | Mostra o negócio 20392 (João Almeida, etapa Novo), criado em 28/10 00:33:11. | Cópia de arquivo de estado de outra pasta, de uma versão **anterior** do WF01; 391 dos 392 negócios são dados fictícios do desafio, sem relação com o teste (ver Segurança). Não prova reenvio do mesmo `event_id`. |

O teste de 28/10 (negócio 20392) tinha três prints, hoje retirados do pacote. A prova que resta dele é o estado do CRM acima, mais a
[auditoria](01-auditoria/auditoria-2026-10-28.md). A prova atual do WF01 é o teste T1.005 (execução 355), com o estado final do CRM conferido.

Resumo: **teste comercial aprovado (execução 355)**. Não afirma que todos os cenários foram testados.

## 03-workflow-02

| Arquivo | Descrição | Resultado | Limitações |
|---|---|---|---|
| [wf02-execucao-356.md](03-workflow-02/wf02-execucao-356.md) | Execução 356 do WF02 (corrigido v2, `fcMKsKzpcdAMKnr0`), 29/10 às 13:17: nós executados, SQLite e CRM antes e depois. | **Aprovada para vincular negócio existente**: negócio 20395 localizado pelo e-mail, "Vincular Negócio Existente" executou, `sync_eventos` do evento 005 passou de `pendente` para `sincronizado` com `deal_id` 20395, CRM continua com 395. | Só o ramo "negócio já existe". O ramo de criação por POST, o de erro e a conciliação de vários eventos não foram executados (o arquivo lista os nós que não rodaram). |
| [wf02-execucao-356.json](03-workflow-02/wf02-execucao-356.json) | Mesmos dados em formato estruturado. | Idêntico ao relato. | Mesmas limitações. |

## 04-workflow-03

| Arquivo | Descrição | Resultado | Limitações |
|---|---|---|---|
| [validacao-resumo-semanal-2026-10-12.md](04-workflow-03/validacao-resumo-semanal-2026-10-12.md) | Compara o cálculo (`solucao/scripts/resumo_semanal.py`) com a apuração histórica, para 12/10/2026 08:00, sobre uma **cópia** do banco original e o lote do webhook. | **23 de 23 indicadores conferem** (funil 391, 187 atualizados, 142 criados, 136 pedidos comerciais, 12 sem correspondência, 68 sem retorno vencido e mais 17 de apoio). Original e cópia com o mesmo SHA-256 antes e depois. | Valida o **cálculo**, não o workflow do n8n. A classificação de pedidos é uma regra por texto, não validada por pessoas. Mediana de 2,08 h úteis (definição estatística), contra 2,15 na apuração antiga. |
| [resumo-semanal-2026-10-12.json](04-workflow-03/resumo-semanal-2026-10-12.json) | Saída completa do cálculo, separada em comprovados, estimativas, dados incompletos e limitações. | Base dos números acima. | Traz nomes, telefones e e-mails fictícios de leads do lote. |
| [resumo-semanal-2026-10-12.txt](04-workflow-03/resumo-semanal-2026-10-12.txt) | Texto em linguagem simples para a gestora. | Exemplo do resumo de 12/10. | Mesmos dados fictícios; lista 12 pedidos ausentes com telefone. |
| *(sem arquivo)* e-mail de teste de **29/10 às 14:53** | O recebimento foi confirmado pela autora no Gmail, em teste manual. O print foi retirado do pacote (dado pessoal). | Sem arquivo, o recebimento é **declaração da autora**, não prova verificável. | O print mostrava o corpo cortado e nenhum ID de execução do n8n, então nunca provou que o envio saiu do WF03 nem do agendamento. O resumo era da semana 19 a 25/10 com **0 negócios** e o aviso "ATENÇÃO: cópia do CRM só tem registros até 2026-10-11". |

**Testes automatizados:** 25 testes aprovados (`py -m unittest solucao/scripts/test_resumo_semanal.py`). A saída não está arquivada
como arquivo: o resultado está no [log de decisões](../../log-de-decisoes.md) e pode ser reproduzido pelo comando.

Resumo: **cálculo histórico validado, 25 testes automatizados aprovados e e-mail recebido em teste manual.**
O WF03 está importado e teve duas execuções manuais com sucesso e e-mail aceito (357 às 14:53 e 359 às 16:19, lidas no n8n). **Agendamento automático ainda não comprovado** (workflow inativo; fuso do workflow importado diferente de Brasília) e **dados do CRM no SQLite desatualizados** (último registro em 11/10/2026).

## 05-testes-banco

| Arquivo | Descrição | Resultado | Limitações |
|---|---|---|---|
| [registros-de-teste-banco.md](05-testes-banco/registros-de-teste-banco.md) | O que `mesa_certa.db` tem a mais que `mesa_certa.original.db`: tabela `sync_eventos`, coluna `classificacao`, `pedidos_formulario` ids 101 a 105 e os negócios 20392 a 20395 do CRM. | `mesa_certa.original.db` intacto (SHA-256 `F545271F…40D6`). | Última gravação do arquivo em 29/10 às 13:28; registros criados depois não foram acrescentados. Explica como voltar ao estado inicial. |

## Segurança e dados pessoais

Verificação feita em 29/10/2026 sobre todos os arquivos desta pasta. Nenhum valor secreto é reproduzido aqui.

| Item | Situação | Ação proposta |
|---|---|---|
| Segredo HMAC | **Não aparece** em nenhum arquivo de texto das evidências. | Nenhuma. |
| Token do CRM | **Não aparece** em nenhum arquivo restante. O único print que o mostrava (`post.png`) foi retirado. | Nenhuma. |
| E-mail pessoal | O print `email-evidencia.png` (endereço de e-mail real da autora e foto de perfil) **foi retirado do pacote** pela autora. | Nenhuma no pacote. Confirmar se o arquivo não está no histórico do GitHub (ver README raiz, seção 7). |
| Nomes, e-mails e telefones | Os dos JSON e do texto do resumo são do **conjunto fictício do desafio**. A exceção é o e-mail de teste `t1.comercial.005@teste-mesacerta.example`, criado nos testes. | Opcional: reduzir `crm-estado-teste-joao-almeida-20392.json` ao negócio 20392 (hoje tem 392 negócios fictícios). |
| Outros segredos | Nenhuma senha, segredo HMAC, Bearer ou chave de API nos arquivos restantes. | Nenhuma. |

## Reprodução

```powershell
py -m unittest solucao/scripts/test_resumo_semanal.py -v                  # 25 testes
$env:MESA_CERTA_HMAC_SECRET = "<segredo do desafio>"                       # só para conferir as assinaturas do lote
py solucao\scripts\validar_resumo_historico.py --saida-dir solucao\evidencias\04-workflow-03
```
