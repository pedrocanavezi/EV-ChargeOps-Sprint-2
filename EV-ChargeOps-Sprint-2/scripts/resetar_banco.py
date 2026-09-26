"""Apaga apenas o banco local de demonstracao para recria-lo no proximo uso."""

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
BANCO = RAIZ / "data" / "ev_chargeops.db"

if BANCO.exists():
    BANCO.unlink()
    print("Banco local removido. Abra o aplicativo para recriar os dados de exemplo.")
else:
    print("O banco local ainda não existe.")
