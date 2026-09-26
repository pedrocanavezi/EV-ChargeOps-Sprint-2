# Decisões técnicas — Sprint 2

## Objetivo

Transformar a pesquisa da Sprint 1 em um protótipo que possa ser executado e
demonstrado sem acesso ao carregador físico da GoodWe.

## Stack escolhida

- Python 3.11 ou superior;
- Streamlit para a interface;
- SQLite para os dados;
- pandas apenas para tabelas e gráficos do painel;
- biblioteca padrão do Python para rateio, CSV e algoritmo KNN.

## Motivo da escolha

A Sprint 1 não fechou a stack. Python foi escolhido porque reduz a quantidade
de código necessária e permite concentrar a entrega no que vale mais pontos:
lógica central, IA integrada e evidência de funcionamento.

O SQLite evita a instalação de um servidor de banco durante a apresentação. O
Streamlit permite iniciar o protótipo com um único comando.

## Desvio em relação ao plano inicial

Não houve mudança no objetivo. O plano citava uma interface web ou uma API
documentada como opções. A equipe escolheu a interface web porque ela mostra o
fluxo completo com mais clareza durante o pitch.

A integração GoodWe/SEMS+ continua fora do escopo porque ainda não há acesso a
uma API, conta de testes ou equipamento físico. O CSV representa a entrada que
poderia ser trocada por uma integração oficial no futuro.

## IA escolhida

Foi criado um detector de anomalias por distância dos vizinhos mais próximos.
Ele não precisa de classes prontas ou de exemplos marcados como fraude. A IA
aprende o padrão com as sessões já registradas e gera um score para cada nova
sessão.

Regras operacionais complementam o modelo para casos que já são conhecidos,
como uma potência média acima do limite do carregador. A IA não altera valores
financeiros.

## Regra financeira

Todos os valores usam `Decimal`. O sistema arredonda energia, taxa percentual e
total para dois centavos com `ROUND_HALF_UP`. Uma sessão pendente não gera
cobrança.

