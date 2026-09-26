"""Abre todas as páginas do Streamlit e testa o formulário principal."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest


RAIZ = Path(__file__).resolve().parents[1]
PAGINAS = [
    "Visão geral",
    "Nova sessão",
    "Importar CSV",
    "Sessões e rateio",
    "Módulo de IA",
]


def validar() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        os.environ["EV_CHARGEOPS_DB"] = str(Path(pasta) / "interface.db")
        app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()

        for pagina in PAGINAS:
            app.sidebar.radio[0].set_value(pagina).run()
            if app.exception:
                raise RuntimeError(f"Erro na página {pagina}: {app.exception}")
            print(f"OK: {pagina}")

        app.sidebar.radio[0].set_value("Nova sessão").run()
        app.text_input[0].set_value("UI-TEST-001")
        app.text_input[3].set_value("Teste de interface")
        app.button[0].click().run()

        if app.exception:
            raise RuntimeError(f"Erro ao enviar o formulário: {app.exception}")
        if not app.success or "UI-TEST-001" not in app.success[0].value:
            raise RuntimeError("O formulário não confirmou o registro da sessão.")
        print("OK: formulário, rateio, gravação e análise de IA")


if __name__ == "__main__":
    validar()
