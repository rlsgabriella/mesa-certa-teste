# Teste técnico: Analista de Dados e Automação (time comercial)

**Prazo:** 3 dias corridos a partir do recebimento. **Tempo de trabalho estimado:** de 6 a 7 horas. Como dividir esse tempo entre os problemas é uma decisão sua.
**Ferramentas:** use o que quiser, inclusive IA em tudo. Use o modelo e o assistente de IA da sua preferência. A empresa não fornece modelo, chave nem acesso, e não reembolsa o uso. O volume de IA que o teste pede é pequeno: são cerca de 300 mensagens de texto no total. Na conversa final você explica cada decisão, linha por linha se pedirmos.

---

## O cenário

Você acabou de entrar na Mesa Certa, uma empresa fictícia de software para restaurantes. Seu trabalho é facilitar a vida da gestora comercial, que não é da área de tecnologia: dar a ela controle dos dados e respostas que hoje ela não consegue ter sozinha.

No seu primeiro dia ela te mandou esta mensagem de voz. Segue a transcrição, do jeito que ela falou.

> Oi, tudo bem? Que bom que você chegou, de verdade. Deixa eu te contar como é minha rotina, porque eu preciso muito de ajuda e eu não sou da área de tecnologia, então vou falar do jeito que eu falo.
>
> Toda manhã eu abro o CRM e fico tentando entender como tá o time. Quantos negócios eu tenho em cada fase, quantos ainda tão como novo, quantos já viraram reunião, quantos eu já perdi. Hoje eu conto no olho, filtrando, e sempre acho que errei. Eu só queria isso na mão, rápido, sem ficar contando.
>
> Aí teve a reunião de pipeline de ontem. O diretor perguntou quantos pedidos de demonstração a gente recebeu na semana passada, de segunda dia 5 até domingo dia 11. Eu falei 187, que foi o que deu na minha planilha, que eu tirei do CRM. E o pessoal do marketing ficou com cara de quem não concordava, falou que o número deles não era esse, e a gente ficou ali uns dez minutos discutindo número. Eu fiquei com vergonha. Eu não sei te explicar de onde sai a diferença, e eu queria chegar na próxima reunião sabendo qual é o número certo e conseguindo explicar o porquê, de um jeito que o diretor entenda.
>
> Outra coisa que me tira do sério. A gente combinou que quem pede demonstração tem que receber ligação em até quatro horas de trabalho, né, horário comercial, de segunda a sexta, das oito às seis. Só que toda semana tem cliente reclamando que ninguém retornou. Eu acho que é o SDR 2, ele é mais devagar, mas eu não consigo provar e não quero acusar ninguém sem ter número. Queria saber de verdade quem tá atrasando e quanto, e quem tá sem retorno agora, hoje, pra eu cobrar hoje.
>
> E tem o seguinte. O marketing jura de pé junto que manda tudo certinho, mas tem pedido que eu nunca vi chegar no CRM, o cliente liga reclamando que pediu e ninguém falou com ele. Ao mesmo tempo tem um monte de coisa na minha fila que não é venda: gente pedindo suporte, gente querendo me vender embalagem, e até teste que o pessoal de lá faz. Meu time perde tempo com isso. E eu queria que o time nem precisasse mudar o jeito que usa o CRM, eles já reclamam demais de qualquer mudança.
>
> Por fim, toda segunda de manhã eu queria receber um resumo de como foi a semana, sozinho, sem eu precisar pedir pra ninguém e sem eu ter que abrir mais um sistema. No Slack, no e-mail, onde for mais fácil, tanto faz, você que sabe. Se eu pudesse até perguntar alguma coisa depois e ele responder, ia ser incrível, mas isso é sonho meu.
>
> É isso, acho que falei demais. Qualquer coisa que eu esqueci, você vai descobrindo no meio do caminho.

## O que fazer

Ela fala de vários problemas, e nem todos aparecem como pergunta. Identifique cada um, decida a ordem e quanto esforço cada um merece (eles não têm o mesmo tamanho) e resolva.

Você não pode perguntar nada a ela. Escreva as suposições que fez.

Considere que **hoje é segunda-feira, 12/10, 08:00 (Brasília)**. Os dados do CRM refletem esse momento.

## O que está na pasta

| Arquivo | O que é |
|---|---|
| `mesa_certa.db` | Banco SQLite. **Faça uma cópia antes de começar** (`mesa_certa.original.db`) para poder repetir do zero |
| `planilha-chefia.csv` | A planilha da gestora, por dia, com o total que ela levou à reunião |
| `webhook/` | O jeito como o marketing entrega os pedidos do formulário (remetente e documentação) |
| `crm-mock/` | O CRM de mentira, com API REST e documentação |

### O banco

- `pedidos_formulario`: o que o formulário do marketing enviou. Já contém a semana de 28/09 a 04/10. O que chegar pelo webhook entra aqui. `criado_em` está em **UTC**.
- `negocios_crm`: cópia dos negócios do CRM. Horários em **Brasília**.
- `historico_etapas`: cada mudança de etapa de cada negócio, em horário de Brasília.

As etapas de um negócio são `Novo`, `Contato`, `Reunião marcada`, `Reunião realizada` e `Perdido`. O SDR faz o primeiro contato e marca a reunião. O closer faz a demonstração.

Os dados refletem a bagunça de uma operação real. Tome as decisões que fizerem sentido e registre cada uma.

## O que entregar

Uma única entrega, numa pasta compactada ou num repositório, sem chaves de acesso.

1. **`problemas.md`**: os problemas que você identificou na fala dela, na ordem em que os resolveu. Diga também o que decidiu **não** resolver e por quê.
2. **`respostas.md`**: para cada problema que tem resposta em número ou lista, a resposta como você a daria a ela, em linguagem simples e sem jargão. Inclua a definição que você usou e o que os dados não permitem afirmar.
3. **`solucao/`**: o que roda sozinho. A forma é livre: planilha com painel, banco com dashboard, bot no Slack, agente que responde perguntas, automações soltas, ou uma combinação. Ela precisa conseguir usar sozinha, toda semana, sem pedir a ninguém e sem o time mudar o jeito de usar o CRM. Mostre a evidência de que funcionou olhando o **estado final no CRM**, e não só o log da sua ferramenta. Se você usar IA em alguma parte, diga onde, por que ali e como mediu se ela acerta. Se houver mais de um jeito de resolver, escolha um, justifique e diga o que descartou.
4. **`suposicoes.md`**: o que você assumiu por não poder perguntar, e as 5 perguntas que faria a ela.
5. **`como-assumir.md`** (1 página técnica, para quem for continuar) e **`guia-para-ela.md`** (meia página, na linguagem dela: o que recebe, quando e o que fazer se algo não vier).
6. **Pacote do assistente de IA de código que você usou**, para que outra pessoa continue o trabalho com a mesma ferramenta. Quatro peças:
   - as instruções fixas do projeto, que o assistente lê sempre (por exemplo `CLAUDE.md`, `AGENTS.md` ou o equivalente da sua ferramenta);
   - um procedimento reutilizável que o assistente carrega só quando o pedido combina (por exemplo uma skill ou o equivalente);
   - uma checagem automática, disparada por um evento do trabalho, que seja útil neste projeto (por exemplo um hook ou o equivalente; se a ferramenta não tiver, descreva como você faria com outro meio);
   - `quando-usar-o-que.md` (3 linhas: quando você usaria o chat, um assistente que age no projeto ou um script agendado neste projeto).
7. **`log-de-decisoes.md`**: linhas com horário, escritas enquanto trabalha: o que você decidiu, o que a IA sugeriu, o que você recusou e por quê.

Dúvidas sobre o enunciado podem ser feitas por escrito. Dúvidas sobre os dados fazem parte do teste.
