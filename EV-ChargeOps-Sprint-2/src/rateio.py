"""Regras financeiras do EV ChargeOps.

O módulo usa Decimal para que os valores de cobrança não sofram com as
imprecisões comuns de números de ponto flutuante.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENTAVO = Decimal("0.01")


def _decimal(valor: object, nome: str) -> Decimal:
    try:
        numero = Decimal(str(valor if valor not in (None, "") else 0))
    except (InvalidOperation, ValueError) as erro:
        raise ValueError(f"{nome} deve ser um número válido.") from erro

    if numero < 0:
        raise ValueError(f"{nome} não pode ser negativo.")
    return numero


def _moeda(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def formatar_reais(valor: Decimal | float | int | str) -> str:
    numero = _moeda(Decimal(str(valor)))
    texto = f"{numero:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


@dataclass(frozen=True)
class ResultadoRateio:
    kwh_consumido: Decimal
    tarifa_kwh: Decimal
    valor_energia: Decimal
    taxa_fixa: Decimal
    percentual_operacional: Decimal
    valor_percentual: Decimal
    valor_taxa: Decimal
    desconto: Decimal
    valor_total: Decimal
    faturavel: bool

    def como_dict(self) -> dict[str, float | bool]:
        dados = asdict(self)
        return {
            chave: float(valor) if isinstance(valor, Decimal) else valor
            for chave, valor in dados.items()
        }

    def memoria_calculo(self) -> str:
        if not self.faturavel:
            return (
                "Sessão pendente ou sem consumo. Nenhuma cobrança foi gerada "
                "até a sessão ser concluída."
            )

        percentual = self.percentual_operacional * Decimal("100")
        return (
            f"Energia: {self.kwh_consumido} kWh x {formatar_reais(self.tarifa_kwh)} "
            f"= {formatar_reais(self.valor_energia)}. "
            f"Taxa: {formatar_reais(self.taxa_fixa)} + {percentual}% da energia "
            f"({formatar_reais(self.valor_percentual)}) = {formatar_reais(self.valor_taxa)}. "
            f"Desconto: {formatar_reais(self.desconto)}. "
            f"Total: {formatar_reais(self.valor_total)}."
        )


def calcular_rateio(
    kwh_consumido: object,
    tarifa_kwh: object,
    taxa_fixa: object = 0,
    percentual_operacional: object = 0,
    desconto: object = 0,
    status: str = "fechada",
) -> ResultadoRateio:
    """Calcula o rateio e arredonda cada parte para centavos.

    Sessões que ainda não foram fechadas não recebem cobrança. A regra evita
    cobrar taxa fixa de uma recarga incompleta ou cancelada.
    """

    kwh = _decimal(kwh_consumido, "kWh consumido")
    tarifa = _decimal(tarifa_kwh, "tarifa por kWh")
    fixa = _decimal(taxa_fixa, "taxa fixa")
    percentual = _decimal(percentual_operacional, "percentual operacional")
    abatimento = _decimal(desconto, "desconto")

    if percentual > 1:
        raise ValueError(
            "Percentual operacional deve ser decimal. Use 0.12 para representar 12%."
        )

    status_normalizado = (status or "").strip().lower()
    faturavel = status_normalizado in {"fechada", "concluida", "concluída"} and kwh > 0

    if not faturavel:
        zero = Decimal("0.00")
        return ResultadoRateio(
            kwh_consumido=kwh,
            tarifa_kwh=tarifa,
            valor_energia=zero,
            taxa_fixa=fixa,
            percentual_operacional=percentual,
            valor_percentual=zero,
            valor_taxa=zero,
            desconto=abatimento,
            valor_total=zero,
            faturavel=False,
        )

    valor_energia = _moeda(kwh * tarifa)
    valor_percentual = _moeda(valor_energia * percentual)
    valor_taxa = _moeda(fixa + valor_percentual)
    valor_total = _moeda(valor_energia + valor_taxa - abatimento)
    valor_total = max(valor_total, Decimal("0.00"))

    return ResultadoRateio(
        kwh_consumido=kwh,
        tarifa_kwh=tarifa,
        valor_energia=valor_energia,
        taxa_fixa=fixa,
        percentual_operacional=percentual,
        valor_percentual=valor_percentual,
        valor_taxa=valor_taxa,
        desconto=abatimento,
        valor_total=valor_total,
        faturavel=True,
    )
