"""Persistência SQLite do EV ChargeOps."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class Banco:
    def __init__(self, caminho: str | Path = "data/ev_chargeops.db") -> None:
        self.caminho = str(caminho)
        Path(self.caminho).parent.mkdir(parents=True, exist_ok=True)

    def conectar(self) -> sqlite3.Connection:
        conexao = sqlite3.connect(self.caminho)
        conexao.row_factory = sqlite3.Row
        return conexao

    def criar_tabelas(self) -> None:
        with self.conectar() as conexao:
            conexao.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessoes (
                    sessao_id TEXT PRIMARY KEY,
                    local TEXT NOT NULL,
                    carregador TEXT NOT NULL,
                    usuario TEXT NOT NULL,
                    unidade TEXT,
                    veiculo TEXT,
                    placa TEXT,
                    inicio TEXT NOT NULL,
                    fim TEXT,
                    kwh_consumido REAL NOT NULL,
                    tarifa_kwh REAL NOT NULL,
                    taxa_fixa REAL NOT NULL DEFAULT 0,
                    percentual_operacional REAL NOT NULL DEFAULT 0,
                    desconto REAL NOT NULL DEFAULT 0,
                    valor_energia REAL NOT NULL DEFAULT 0,
                    valor_taxa REAL NOT NULL DEFAULT 0,
                    valor_total REAL NOT NULL DEFAULT 0,
                    memoria_calculo TEXT NOT NULL,
                    status TEXT NOT NULL,
                    origem_dado TEXT NOT NULL,
                    ia_score REAL NOT NULL DEFAULT 0,
                    ia_anomalia INTEGER NOT NULL DEFAULT 0,
                    ia_motivos TEXT NOT NULL DEFAULT '[]',
                    ia_metodo TEXT NOT NULL DEFAULT 'Regras operacionais',
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_sessoes_inicio ON sessoes(inicio);
                CREATE INDEX IF NOT EXISTS idx_sessoes_usuario ON sessoes(usuario);
                CREATE INDEX IF NOT EXISTS idx_sessoes_anomalia ON sessoes(ia_anomalia);
                """
            )

    def quantidade(self) -> int:
        with self.conectar() as conexao:
            return int(conexao.execute("SELECT COUNT(*) FROM sessoes").fetchone()[0])

    def existe(self, sessao_id: str) -> bool:
        with self.conectar() as conexao:
            linha = conexao.execute(
                "SELECT 1 FROM sessoes WHERE sessao_id = ?", (sessao_id,)
            ).fetchone()
            return linha is not None

    def salvar_sessao(self, dados: dict, substituir: bool = False) -> None:
        comando = "INSERT OR REPLACE" if substituir else "INSERT"
        campos = [
            "sessao_id",
            "local",
            "carregador",
            "usuario",
            "unidade",
            "veiculo",
            "placa",
            "inicio",
            "fim",
            "kwh_consumido",
            "tarifa_kwh",
            "taxa_fixa",
            "percentual_operacional",
            "desconto",
            "valor_energia",
            "valor_taxa",
            "valor_total",
            "memoria_calculo",
            "status",
            "origem_dado",
            "ia_score",
            "ia_anomalia",
            "ia_motivos",
            "ia_metodo",
        ]
        valores = []
        for campo in campos:
            valor = dados.get(campo)
            if campo == "ia_motivos":
                valor = json.dumps(valor or [], ensure_ascii=False)
            if campo == "ia_anomalia":
                valor = int(bool(valor))
            valores.append(valor)

        marcadores = ", ".join("?" for _ in campos)
        with self.conectar() as conexao:
            conexao.execute(
                f"{comando} INTO sessoes ({', '.join(campos)}) VALUES ({marcadores})",
                valores,
            )

    def atualizar_ia(self, sessao_id: str, analise: dict) -> None:
        with self.conectar() as conexao:
            conexao.execute(
                """
                UPDATE sessoes
                SET ia_score = ?, ia_anomalia = ?, ia_motivos = ?, ia_metodo = ?
                WHERE sessao_id = ?
                """,
                (
                    analise["score"],
                    int(bool(analise["anomalia"])),
                    json.dumps(analise["motivos"], ensure_ascii=False),
                    analise["metodo"],
                    sessao_id,
                ),
            )

    def listar_sessoes(self) -> list[dict]:
        with self.conectar() as conexao:
            linhas = conexao.execute(
                "SELECT * FROM sessoes ORDER BY inicio DESC, sessao_id DESC"
            ).fetchall()
        return [self._converter(linha) for linha in linhas]

    def buscar_sessao(self, sessao_id: str) -> dict | None:
        with self.conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM sessoes WHERE sessao_id = ?", (sessao_id,)
            ).fetchone()
        return self._converter(linha) if linha else None

    def metricas(self) -> dict[str, float | int]:
        with self.conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT
                    COUNT(*) AS sessoes,
                    COALESCE(SUM(kwh_consumido), 0) AS kwh,
                    COALESCE(SUM(valor_total), 0) AS total,
                    COALESCE(SUM(ia_anomalia), 0) AS anomalias
                FROM sessoes
                """
            ).fetchone()
        return {
            "sessoes": int(linha["sessoes"]),
            "kwh": float(linha["kwh"]),
            "total": float(linha["total"]),
            "anomalias": int(linha["anomalias"]),
        }

    @staticmethod
    def _converter(linha: sqlite3.Row) -> dict:
        dados = dict(linha)
        try:
            dados["ia_motivos"] = json.loads(dados.get("ia_motivos") or "[]")
        except json.JSONDecodeError:
            dados["ia_motivos"] = []
        dados["ia_anomalia"] = bool(dados.get("ia_anomalia"))
        return dados
