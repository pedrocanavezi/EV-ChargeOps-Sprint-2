# Validação do protótipo

Validação executada novamente em **26/09/2026**.

## Resultado

- **10 testes automatizados aprovados**;
- cinco páginas do Streamlit abertas sem exceções;
- formulário testado com gravação, cálculo e análise de IA;
- servidor iniciado localmente e rota de saúde respondendo `200 ok`;
- 12 sessões de exemplo processadas sem erro;
- 207,05 kWh consolidados;
- R$ 240,12 calculados;
- uma anomalia conhecida detectada para demonstração.

## Comandos usados

```bash
python -m py_compile app.py src/*.py scripts/*.py
python -m unittest discover -s tests -v
python scripts/validar_interface.py
python scripts/gerar_evidencias.py
python -m streamlit run app.py
```

O arquivo [`resultado-demo.md`](resultado-demo.md) mostra a saída do fluxo de
importação, recálculo, gravação, análise e exportação.
