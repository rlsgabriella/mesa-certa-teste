# Teste Técnico — Mesa Certa

## 1. Objetivo

Desenvolver uma integração automatizada entre solicitações
de demonstração recebidas por webhook e um CRM simulado,
utilizando n8n e Python.

A solução busca garantir a segurança, a organização e
o processamento correto dos dados recebidos.

## 2. Tecnologias utilizadas

- n8n — Automação de workflows (implementação principal)
- JavaScript — Validação HMAC nos Code nodes do n8n
- Python — Só para rodar o CRM mock e o remetente do webhook fornecidos pelo desafio
- Git e GitHub — Versionamento e entrega
- Kiro — Ambiente de desenvolvimento com assistência de IA

## 3. Funcionamento da integração

O workflow foi estruturado com as seguintes etapas:

1. Recebimento de eventos via webhook.
2. Validação da assinatura HMAC.
3. Verificação da autenticidade da requisição.
4. Normalização e preparação dos campos recebidos.
5. Consulta de contatos existentes no CRM via HTTP GET.
6. Verificação de duplicidade por e-mail.
7. Encaminhamento de novos contatos para criação via HTTP POST.

## 4. Estado atual do desenvolvimento

### Implementado e parcialmente testado

- Recebimento de eventos via webhook.
- Validação de assinatura HMAC.
- Condição IF para assinaturas válidas.
- Preparação dos dados com Edit Fields.
- Consulta HTTP GET ao CRM.
- Verificação de contatos existentes.
- Criação de contatos via HTTP POST: testada com 1 evento
  (`evt_500110`, negócio 20392; ver `solucao/evidencias/`).

### Pendente de validação ou implementação

- Classificação de leads.
- Tratamento de erros HTTP.
- Retentativas com backoff.
- Idempotência de eventos.
- Testes completos com o lote fornecido.
- Coleta de evidências do estado final do CRM.

## 5. Estrutura do repositório

- README.md — Apresentação do projeto.
- problemas.md — Problemas identificados e prioridades.
- respostas.md — Respostas às questões do teste.
- suposicoes.md — Premissas e dúvidas.
- como-assumir.md — Guia técnico de continuidade.
- guia-para-ela.md — Orientações de utilização.
- quando-usar-o-que.md — Orientações sobre uso da IA.
- log-de-decisoes.md — Registro das decisões técnicas.
- solucao/ — Automação em n8n (ver `solucao/README.md`):
  - solucao/workflows/ — Workflows exportados e regras de negócio.
  - solucao/configuracoes/ — Endereços e configuração das credenciais.
  - solucao/evidencias/ — Prints, estado do CRM e auditoria dos dados.
  - solucao/crm-mock-teste/ — Cópia isolada do CRM mock do desafio.
- webhook/ — Remetente e lote do marketing, copiados do desafio sem alteração.
- mesa_certa.db e mesa_certa.original.db — Banco do desafio e cópia intacta.

## 6. Segurança

A integração utiliza validação HMAC para verificar
a autenticidade dos eventos recebidos.

Credenciais, tokens e segredos de autenticação não
devem ser publicados no repositório. No n8n eles ficam
em credenciais (ver `solucao/configuracoes/README.md`).

Os únicos valores desse tipo no repositório são os de
teste publicados pelo próprio desafio, em arquivos
copiados sem alteração (`webhook/README.md` e
`solucao/crm-mock-teste/crm-mock.py`).

## 7. Documentação

A documentação será atualizada conforme o desenvolvimento,
os testes e a validação das funcionalidades.

## 8. Status

Projeto em desenvolvimento.

A conclusão será confirmada após os testes de integração,
a verificação dos registros no CRM e a documentação
das evidências.