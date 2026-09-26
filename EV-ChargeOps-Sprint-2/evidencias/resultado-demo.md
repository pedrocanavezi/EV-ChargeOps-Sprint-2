# Evidência de execução — EV ChargeOps

Este arquivo foi gerado pelo script `scripts/gerar_evidencias.py`.

## Resultado do fluxo completo

- Sessões importadas: **12**
- Sessões armazenadas: **12**
- Energia registrada: **207.05 kWh**
- Valor total calculado: **R$ 240,12**
- Sessões sinalizadas pela IA: **1**
- Erros durante a importação: **0**

## Exemplo de memória de cálculo

Sessão **S-0001**: Energia: 18.4 kWh x R$ 0,92 = R$ 16,93. Taxa: R$ 2,00 + 12.00% da energia (R$ 2,03) = R$ 4,03. Desconto: R$ 0,00. Total: R$ 20,96.

## Anomalias encontradas

- **S-0011** — score 100.0: A potência média estimada foi 65.0 kW, acima do limite de referência de 22 kW. O padrão de consumo, duração, potência e horário ficou distante das sessões históricas mais parecidas.

## Verificações realizadas

1. Leitura do CSV.
2. Validação e gravação no SQLite.
3. Recálculo do rateio com `Decimal`.
4. Geração da memória de cálculo.
5. Análise de todas as sessões pelo módulo de IA.
6. Exportação do relatório consolidado.
