"""Módulo local de inteligência artificial do EV ChargeOps.

O detector usa distância entre vizinhos próximos (KNN) para comparar uma
sessão com o histórico. Não precisa de chave de API e pode ser explicado e
executado durante a avaliação presencial.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import sqrt
from statistics import mean, pstdev
from typing import Iterable


@dataclass(frozen=True)
class AnaliseIA:
    score: float
    anomalia: bool
    motivos: list[str]
    metodo: str

    def resumo(self) -> str:
        if not self.motivos:
            return "A sessão está dentro do padrão conhecido."
        return " ".join(self.motivos)


def _data(valor: object) -> datetime | None:
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor
    texto = str(valor).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        return None


def _duracao_horas(sessao: dict) -> float | None:
    inicio = _data(sessao.get("inicio"))
    fim = _data(sessao.get("fim"))
    if not inicio or not fim:
        return None
    return (fim - inicio).total_seconds() / 3600


def _vetor(sessao: dict) -> list[float] | None:
    duracao = _duracao_horas(sessao)
    inicio = _data(sessao.get("inicio"))
    kwh = float(sessao.get("kwh_consumido") or 0)
    if duracao is None or duracao <= 0 or not inicio or kwh <= 0:
        return None
    potencia_media = kwh / duracao
    hora_decimal = inicio.hour + inicio.minute / 60
    return [kwh, duracao, potencia_media, hora_decimal]


def _score_knn(sessao: dict, historico: list[dict]) -> float | None:
    alvo = _vetor(sessao)
    vetores = [vetor for item in historico if (vetor := _vetor(item)) is not None]
    if alvo is None or len(vetores) < 4:
        return None

    colunas = list(zip(*vetores))
    medias = [mean(coluna) for coluna in colunas]
    desvios = [pstdev(coluna) or 1.0 for coluna in colunas]

    def normalizar(vetor: list[float]) -> list[float]:
        return [(valor - medias[i]) / desvios[i] for i, valor in enumerate(vetor)]

    alvo_normalizado = normalizar(alvo)
    distancias = []
    for vetor in vetores:
        outro = normalizar(vetor)
        distancia = sqrt(sum((a - b) ** 2 for a, b in zip(alvo_normalizado, outro)))
        distancias.append(distancia)

    quantidade_vizinhos = min(3, len(distancias))
    media_vizinhos = mean(sorted(distancias)[:quantidade_vizinhos])

    # A distância é convertida para uma escala simples de 0 a 100.
    return round(min(100.0, media_vizinhos * 28), 1)


def analisar_sessao(
    sessao: dict,
    historico: Iterable[dict],
    potencia_limite_kw: float = 22.0,
) -> AnaliseIA:
    """Analisa a sessão sem alterar o valor financeiro calculado."""

    historico_lista = [
        item
        for item in historico
        if item.get("sessao_id") != sessao.get("sessao_id")
        and str(item.get("status", "")).lower() in {"fechada", "concluida", "concluída"}
    ]
    motivos: list[str] = []
    score_regras = 0.0
    duracao = _duracao_horas(sessao)
    kwh = float(sessao.get("kwh_consumido") or 0)
    status = str(sessao.get("status") or "").lower()

    if status in {"fechada", "concluida", "concluída"} and duracao is None:
        score_regras = max(score_regras, 85)
        motivos.append("A sessão foi fechada sem horário final válido.")

    if duracao is not None and duracao <= 0:
        score_regras = max(score_regras, 100)
        motivos.append("O horário final não pode ser anterior ao horário inicial.")

    if duracao is not None and duracao > 0:
        potencia_media = kwh / duracao
        if kwh == 0 and duracao >= 0.5:
            score_regras = max(score_regras, 85)
            motivos.append("Houve tempo conectado, mas o consumo ficou em zero.")
        if potencia_media > potencia_limite_kw * 1.10:
            score_regras = max(score_regras, 98)
            motivos.append(
                f"A potência média estimada foi {potencia_media:.1f} kW, acima do limite "
                f"de referência de {potencia_limite_kw:.0f} kW."
            )
        if duracao > 12:
            score_regras = max(score_regras, 75)
            motivos.append("A duração passou de 12 horas e precisa de revisão.")

    if kwh > 80:
        score_regras = max(score_regras, 80)
        motivos.append("O consumo passou de 80 kWh em uma única sessão.")

    score_knn = _score_knn(sessao, historico_lista)
    metodo = "Regras operacionais"
    score = score_regras

    if score_knn is not None:
        metodo = "KNN não supervisionado + regras operacionais"
        score = max(score, score_knn)
        if score_knn >= 60:
            motivos.append(
                "O padrão de consumo, duração, potência e horário ficou distante "
                "das sessões históricas mais parecidas."
            )

    score = round(min(100.0, score), 1)
    return AnaliseIA(
        score=score,
        anomalia=score >= 60,
        motivos=motivos,
        metodo=metodo,
    )


def prever_demanda(historico: Iterable[dict], dias: int = 7) -> list[dict]:
    """Cria uma previsão curta pela média diária e pelo padrão do dia da semana."""

    consumo_por_data: dict[datetime.date, float] = {}
    for sessao in historico:
        inicio = _data(sessao.get("inicio"))
        kwh = float(sessao.get("kwh_consumido") or 0)
        if inicio and kwh > 0 and str(sessao.get("status", "")).lower() == "fechada":
            consumo_por_data[inicio.date()] = consumo_por_data.get(inicio.date(), 0) + kwh

    if not consumo_por_data:
        return []

    valores = list(consumo_por_data.values())
    media_geral = mean(valores)
    por_dia_semana: dict[int, list[float]] = {}
    for data_ref, consumo in consumo_por_data.items():
        por_dia_semana.setdefault(data_ref.weekday(), []).append(consumo)

    ultima_data = max(consumo_por_data)
    previsao = []
    for deslocamento in range(1, dias + 1):
        data_futura = ultima_data + timedelta(days=deslocamento)
        amostras = por_dia_semana.get(data_futura.weekday(), [])
        estimativa = mean(amostras) if amostras else media_geral
        previsao.append(
            {
                "data": data_futura.isoformat(),
                "kwh_previsto": round(max(0, estimativa), 2),
            }
        )
    return previsao
