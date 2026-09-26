"""Executa o fluxo completo e gera evidencias reproduziveis da Sprint 2."""

from __future__ import annotations

import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.database import Banco  # noqa: E402
from src.rateio import formatar_reais  # noqa: E402
from src.services import gerar_csv_relatorio, importar_csv_arquivo  # noqa: E402


def main() -> None:
    pasta = RAIZ / "evidencias"
    pasta.mkdir(exist_ok=True)
    banco_demo = pasta / "demo.db"
    if banco_demo.exists():
        banco_demo.unlink()

    banco = Banco(banco_demo)
    banco.criar_tabelas()
    resultado = importar_csv_arquivo(
        banco,
        RAIZ / "assets" / "data" / "exemplos-sessoes.csv",
    )
    sessoes = banco.listar_sessoes()
    metricas = banco.metricas()
    anomalias = [sessao for sessao in sessoes if sessao["ia_anomalia"]]
    exemplo = banco.buscar_sessao("S-0001")

    linhas = [
        "# Evidência de execução — EV ChargeOps",
        "",
        "Este arquivo foi gerado pelo script `scripts/gerar_evidencias.py`.",
        "",
        "## Resultado do fluxo completo",
        "",
        f"- Sessões importadas: **{len(resultado['importadas'])}**",
        f"- Sessões armazenadas: **{metricas['sessoes']}**",
        f"- Energia registrada: **{metricas['kwh']:.2f} kWh**",
        f"- Valor total calculado: **{formatar_reais(metricas['total'])}**",
        f"- Sessões sinalizadas pela IA: **{metricas['anomalias']}**",
        f"- Erros durante a importação: **{len(resultado['erros'])}**",
        "",
        "## Exemplo de memória de cálculo",
        "",
        f"Sessão **{exemplo['sessao_id']}**: {exemplo['memoria_calculo']}",
        "",
        "## Anomalias encontradas",
        "",
    ]

    for sessao in anomalias:
        motivos = " ".join(sessao["ia_motivos"]) or "Padrão fora do esperado."
        linhas.append(
            f"- **{sessao['sessao_id']}** — score {sessao['ia_score']:.1f}: {motivos}"
        )

    linhas.extend(
        [
            "",
            "## Verificações realizadas",
            "",
            "1. Leitura do CSV.",
            "2. Validação e gravação no SQLite.",
            "3. Recálculo do rateio com `Decimal`.",
            "4. Geração da memória de cálculo.",
            "5. Análise de todas as sessões pelo módulo de IA.",
            "6. Exportação do relatório consolidado.",
            "",
        ]
    )

    (pasta / "resultado-demo.md").write_text("\n".join(linhas), encoding="utf-8")
    (pasta / "sessoes-processadas.csv").write_text(
        gerar_csv_relatorio(sessoes), encoding="utf-8"
    )
    print("Evidencias geradas em:", pasta)
    print("Sessoes:", metricas["sessoes"])
    print("Anomalias:", metricas["anomalias"])
    print("Total:", formatar_reais(metricas["total"]))


if __name__ == "__main__":
    main()

