"""Casos de uso que ligam rateio, IA e banco de dados."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from pathlib import Path

from src.database import Banco
from src.ia import analisar_sessao
from src.rateio import calcular_rateio


def _numero(valor: object, padrao: float = 0) -> float:
    if valor in (None, ""):
        return padrao
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if "," in texto and "." not in texto:
        texto = texto.replace(",", ".")
    return float(texto)


def _texto(valor: object, padrao: str = "") -> str:
    return str(valor if valor not in (None, "") else padrao).strip()


def _validar_data(valor: str, obrigatoria: bool = True) -> str | None:
    if not valor:
        if obrigatoria:
            raise ValueError("O horário inicial é obrigatório.")
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).isoformat()
    except ValueError as erro:
        raise ValueError(f"Data inválida: {valor}") from erro


def normalizar_sessao(dados: dict, origem_padrao: str = "manual") -> dict:
    sessao = {
        "sessao_id": _texto(dados.get("sessao_id")) or f"S-{uuid.uuid4().hex[:8].upper()}",
        "local": _texto(dados.get("local")),
        "carregador": _texto(dados.get("carregador")),
        "usuario": _texto(dados.get("usuario")),
        "unidade": _texto(dados.get("unidade")),
        "veiculo": _texto(dados.get("veiculo")),
        "placa": _texto(dados.get("placa")).upper(),
        "inicio": _validar_data(_texto(dados.get("inicio"))),
        "fim": _validar_data(_texto(dados.get("fim")), obrigatoria=False),
        "kwh_consumido": _numero(dados.get("kwh_consumido")),
        "tarifa_kwh": _numero(dados.get("tarifa_kwh"), 0.92),
        "taxa_fixa": _numero(dados.get("taxa_fixa"), 0),
        "percentual_operacional": _numero(dados.get("percentual_operacional"), 0),
        "desconto": _numero(dados.get("desconto"), 0),
        "status": _texto(dados.get("status"), "fechada").lower(),
        "origem_dado": _texto(dados.get("origem_dado"), origem_padrao).lower(),
    }

    faltando = [campo for campo in ("local", "carregador", "usuario") if not sessao[campo]]
    if faltando:
        raise ValueError("Campos obrigatórios ausentes: " + ", ".join(faltando))
    if sessao["kwh_consumido"] < 0:
        raise ValueError("O consumo não pode ser negativo.")
    return sessao


def processar_sessao(
    banco: Banco,
    dados: dict,
    substituir: bool = False,
    origem_padrao: str = "manual",
) -> dict:
    sessao = normalizar_sessao(dados, origem_padrao=origem_padrao)
    if banco.existe(sessao["sessao_id"]) and not substituir:
        raise ValueError(f"A sessão {sessao['sessao_id']} já está cadastrada.")

    rateio = calcular_rateio(
        kwh_consumido=sessao["kwh_consumido"],
        tarifa_kwh=sessao["tarifa_kwh"],
        taxa_fixa=sessao["taxa_fixa"],
        percentual_operacional=sessao["percentual_operacional"],
        desconto=sessao["desconto"],
        status=sessao["status"],
    )
    valores = rateio.como_dict()
    sessao.update(
        {
            "valor_energia": valores["valor_energia"],
            "valor_taxa": valores["valor_taxa"],
            "valor_total": valores["valor_total"],
            "memoria_calculo": rateio.memoria_calculo(),
        }
    )

    analise = analisar_sessao(sessao, banco.listar_sessoes())
    sessao.update(
        {
            "ia_score": analise.score,
            "ia_anomalia": analise.anomalia,
            "ia_motivos": analise.motivos,
            "ia_metodo": analise.metodo,
        }
    )
    banco.salvar_sessao(sessao, substituir=substituir)
    return sessao


def importar_csv_texto(
    banco: Banco,
    conteudo: str,
    substituir: bool = False,
) -> dict[str, object]:
    leitor = csv.DictReader(io.StringIO(conteudo.lstrip("\ufeff")))
    importadas: list[str] = []
    ignoradas: list[str] = []
    erros: list[str] = []

    for numero_linha, linha in enumerate(leitor, start=2):
        sessao_id = _texto(linha.get("sessao_id"), f"linha {numero_linha}")
        try:
            if banco.existe(sessao_id) and not substituir:
                ignoradas.append(sessao_id)
                continue
            salva = processar_sessao(
                banco,
                linha,
                substituir=substituir,
                origem_padrao="csv",
            )
            importadas.append(salva["sessao_id"])
        except (ValueError, TypeError) as erro:
            erros.append(f"Linha {numero_linha} ({sessao_id}): {erro}")

    reanalisar_todas(banco)
    return {"importadas": importadas, "ignoradas": ignoradas, "erros": erros}


def importar_csv_arquivo(
    banco: Banco,
    caminho: str | Path,
    substituir: bool = False,
) -> dict[str, object]:
    conteudo = Path(caminho).read_text(encoding="utf-8")
    return importar_csv_texto(banco, conteudo, substituir=substituir)


def reanalisar_todas(banco: Banco) -> None:
    sessoes = banco.listar_sessoes()
    for sessao in sessoes:
        analise = analisar_sessao(sessao, sessoes)
        banco.atualizar_ia(
            sessao["sessao_id"],
            {
                "score": analise.score,
                "anomalia": analise.anomalia,
                "motivos": analise.motivos,
                "metodo": analise.metodo,
            },
        )


def gerar_csv_relatorio(sessoes: list[dict]) -> str:
    campos = [
        "sessao_id",
        "local",
        "carregador",
        "usuario",
        "unidade",
        "inicio",
        "fim",
        "kwh_consumido",
        "tarifa_kwh",
        "valor_energia",
        "valor_taxa",
        "desconto",
        "valor_total",
        "status",
        "origem_dado",
        "ia_score",
        "ia_anomalia",
    ]
    saida = io.StringIO()
    escritor = csv.DictWriter(saida, fieldnames=campos, extrasaction="ignore")
    escritor.writeheader()
    escritor.writerows(sessoes)
    return saida.getvalue()
