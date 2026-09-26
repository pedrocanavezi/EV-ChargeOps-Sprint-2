# Papel da IA

## Objetivo

A IA entra no EV ChargeOps como apoio para operacao e analise. Ela nao deve substituir medicao, regra de contrato, validacao regulatoria ou aprovacao financeira.

Essa limitacao e importante porque o sistema lida com cobranca. Se a IA alterar valor, inventar leitura ou aprovar desconto sozinha, o administrador perde a capacidade de explicar o fechamento. No MVP, a IA deve trabalhar em cima de dados ja registrados e regras conhecidas.

## Casos de uso

| Caso | Beneficio |
| --- | --- |
| Previsao de demanda | Estimar horarios de maior uso para planejar operacao. |
| Deteccao de anomalias | Sinalizar sessao muito longa, kWh fora do padrao ou dado incompleto. |
| Explicacao de cobranca | Resumir a memoria de calculo para administrador ou usuario. |
| Classificacao de incidentes | Organizar relatos de erro, falha no carregador ou interrupcao. |
| Recomendacao operacional | Sugerir investigacao de manutencao, aumento de potencia ou ajuste de regra. |

## Entradas de dados

- historico de sessoes;
- potencia do carregador;
- horario de inicio e fim;
- kWh consumido;
- usuario, veiculo ou unidade;
- origem do dado: CSV, GoodWe/SEMS+, medidor ou lancamento manual;
- eventos de erro;
- tarifa vigente;
- calendario e clima, apenas em fase futura.

## Saidas esperadas

- alerta de consumo fora do padrao;
- previsao simples por dia da semana e horario;
- resumo mensal da operacao;
- explicacao de cobranca em linguagem simples;
- lista de sessoes com dado faltante antes do fechamento.

## Limites

- IA nao altera valores financeiros sem aprovacao humana.
- IA nao inventa leitura de medidor.
- IA nao substitui regra de rateio documentada.
- IA nao emite parecer regulatorio definitivo.
- IA nao deve expor dados pessoais sem permissao adequada.

## MVP recomendado

1. Comecar com regras deterministicas para anomalias basicas.
2. Gerar resumo textual do fechamento mensal.
3. Criar explicacao de uma sessao com base na memoria de calculo.
4. Evoluir para previsao estatistica quando houver historico suficiente.

## Exemplos de alertas

- Sessao sem leitura final.
- kWh igual a zero com tempo conectado maior que 30 minutos.
- Consumo muito acima do padrao do usuario ou do carregador.
- Carregador com muitas sessoes interrompidas na semana.
- Diferenca entre soma das sessoes e medidor geral acima da tolerancia definida.
