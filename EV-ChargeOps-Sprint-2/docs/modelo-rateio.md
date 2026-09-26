# Modelo de Rateio

## Objetivo

O modelo de rateio calcula quanto cada usuario deve pagar por uma sessao de recarga. A regra precisa ser simples porque o valor pode ser questionado por morador, motorista, administradora ou operador.

Nesta Sprint 01, a base escolhida foi o kWh consumido. Essa escolha e mais defensavel do que cobrar apenas por tempo, porque o custo principal vem da energia entregue. O tempo conectado pode entrar depois como taxa adicional, mas nao deve ser a unica base de cobranca.

## Formula base

```text
valor_energia = kwh_consumido * tarifa_kwh
valor_taxa = taxa_fixa_sessao + (valor_energia * percentual_operacional)
valor_total = valor_energia + valor_taxa - desconto
```

## Campos necessarios

| Campo | Exemplo | Observacao |
| --- | --- | --- |
| kwh_consumido | 18.4 | Deve vir do carregador, medidor, CSV ou leitura validada. |
| tarifa_kwh | 0.92 | Valor configurado por local e vigencia. |
| taxa_fixa_sessao | 2.00 | Opcional, cobre custo operacional minimo. |
| percentual_operacional | 12% | Opcional, cobre manutencao, administracao e infraestrutura. |
| desconto | 0.00 | Opcional, usado para ajuste aprovado, cortesia ou campanha. |

## Exemplo

```text
kwh_consumido = 18.4
tarifa_kwh = R$ 0.92
taxa_fixa_sessao = R$ 2.00
percentual_operacional = 12%
desconto = R$ 0.00

valor_energia = 18.4 * 0.92 = R$ 16.93
valor_taxa = 2.00 + (16.93 * 0.12) = R$ 4.03
valor_total = 16.93 + 4.03 = R$ 20.96
```

## Variacoes de regra

| Cenario | Regra sugerida |
| --- | --- |
| Condominio residencial | Rateio por kWh, com fechamento mensal por unidade. |
| Estacionamento comercial | Preco por kWh mais taxa por sessao ou permanencia. |
| Frota corporativa | Centro de custo por veiculo, motorista ou departamento. |
| Carregador gratuito | Registrar kWh e custo interno, sem cobranca ao usuario. |
| Horario de ponta | Tarifa por faixa horaria, se houver medicao confiavel. |

## Auditoria minima

Para a cobranca ser conferivel, cada sessao deve guardar:

- tarifa usada no momento do calculo;
- leitura inicial e final, quando existir;
- origem do dado: GoodWe/SEMS+, CSV, medidor externo ou lancamento manual;
- usuario ou processo que registrou ajuste;
- regra de taxa operacional aplicada;
- calculo original, mesmo que exista recalculo simulado depois.

## Pontos pendentes

- Definir arredondamento por sessao ou apenas no fechamento mensal.
- Definir tratamento para sessao interrompida.
- Definir tolerancia entre medidor do carregador e medidor geral.
- Definir valor minimo por sessao, se o local quiser usar.
- Definir politica para isencao, cortesia ou erro operacional.
- Validar se a leitura usada para cobranca tem precisao suficiente para o modelo adotado.
