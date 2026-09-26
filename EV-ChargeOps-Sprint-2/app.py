"""Painel web do prototipo EV ChargeOps."""

from __future__ import annotations

import io
import os
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st

from src.database import Banco
from src.ia import prever_demanda
from src.rateio import formatar_reais
from src.services import (
    gerar_csv_relatorio,
    importar_csv_arquivo,
    importar_csv_texto,
    processar_sessao,
)


RAIZ = Path(__file__).resolve().parent
BANCO_PADRAO = Path(
    os.environ.get("EV_CHARGEOPS_DB", str(RAIZ / "data" / "ev_chargeops.db"))
)
CSV_EXEMPLO = RAIZ / "assets" / "data" / "exemplos-sessoes.csv"


st.set_page_config(
    page_title="EV ChargeOps",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
        [data-testid="stMetric"] {
            background: #111827;
            border: 1px solid #243047;
            border-radius: 12px;
            padding: 14px;
        }
        .ev-card {
            background: linear-gradient(135deg, #101827, #162235);
            border: 1px solid #263650;
            border-radius: 14px;
            padding: 18px;
            margin: 8px 0 18px 0;
        }
        .ev-card h3 { margin-top: 0; }
        .ok { color: #4ade80; font-weight: 700; }
        .alerta { color: #fb7185; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def iniciar_banco() -> Banco:
    banco = Banco(BANCO_PADRAO)
    banco.criar_tabelas()
    if banco.quantidade() == 0 and CSV_EXEMPLO.exists():
        importar_csv_arquivo(banco, CSV_EXEMPLO)
    return banco


def tabela_sessoes(sessoes: list[dict]) -> pd.DataFrame:
    if not sessoes:
        return pd.DataFrame()
    tabela = pd.DataFrame(sessoes)
    tabela["analise_ia"] = tabela["ia_anomalia"].map(
        {True: "Revisar", False: "Normal"}
    )
    tabela["valor_total"] = tabela["valor_total"].map(lambda valor: f"R$ {valor:.2f}")
    tabela["kwh_consumido"] = tabela["kwh_consumido"].map(lambda valor: f"{valor:.2f}")
    return tabela[
        [
            "sessao_id",
            "inicio",
            "usuario",
            "local",
            "carregador",
            "kwh_consumido",
            "valor_total",
            "status",
            "origem_dado",
            "analise_ia",
            "ia_score",
        ]
    ].rename(
        columns={
            "sessao_id": "Sessão",
            "inicio": "Início",
            "usuario": "Usuário",
            "local": "Local",
            "carregador": "Carregador",
            "kwh_consumido": "kWh",
            "valor_total": "Total",
            "status": "Status",
            "origem_dado": "Origem",
            "analise_ia": "IA",
            "ia_score": "Score IA",
        }
    )


def pagina_visao_geral(banco: Banco) -> None:
    st.title("EV ChargeOps")
    st.caption("Sessões de recarga, rateio auditável e inteligência operacional.")

    metricas = banco.metricas()
    colunas = st.columns(4)
    colunas[0].metric("Sessões registradas", metricas["sessoes"])
    colunas[1].metric("Energia registrada", f"{metricas['kwh']:.2f} kWh")
    colunas[2].metric("Valor calculado", formatar_reais(metricas["total"]))
    colunas[3].metric("Sessões para revisar", metricas["anomalias"])

    sessoes = banco.listar_sessoes()
    if not sessoes:
        st.info("Nenhuma sessão foi cadastrada.")
        return

    esquerda, direita = st.columns([1.4, 1])
    with esquerda:
        st.subheader("Consumo por usuário")
        dados = pd.DataFrame(sessoes)
        consumo = (
            dados.groupby("usuario", as_index=False)["kwh_consumido"]
            .sum()
            .sort_values("kwh_consumido", ascending=False)
            .set_index("usuario")
        )
        st.bar_chart(consumo, y="kwh_consumido", color="#37d399")

    with direita:
        st.subheader("Situação da IA")
        anomalias = [sessao for sessao in sessoes if sessao["ia_anomalia"]]
        if anomalias:
            st.markdown(
                f'<div class="ev-card"><span class="alerta">{len(anomalias)} sessão(ões) '
                "precisam de revisão humana.</span><br>A IA apenas sinaliza. Ela não altera "
                "a cobrança.</div>",
                unsafe_allow_html=True,
            )
            for sessao in anomalias[:3]:
                st.write(
                    f"**{sessao['sessao_id']} — {sessao['usuario']}**: "
                    + (" ".join(sessao["ia_motivos"]) or "Padrão fora do esperado.")
                )
        else:
            st.markdown(
                '<div class="ev-card"><span class="ok">Nenhuma anomalia detectada.</span></div>',
                unsafe_allow_html=True,
            )

    st.subheader("Sessões recentes")
    st.dataframe(tabela_sessoes(sessoes[:8]), width="stretch", hide_index=True)


def pagina_nova_sessao(banco: Banco) -> None:
    st.title("Registrar nova sessão")
    st.write("Os valores são recalculados pelo sistema. A IA analisa a sessão após o registro.")

    sugestao_id = "S-" + datetime.now().strftime("%m%d%H%M%S")
    with st.form("nova_sessao", clear_on_submit=False):
        a, b, c = st.columns(3)
        sessao_id = a.text_input("Código da sessão", value=sugestao_id)
        local = b.text_input("Local", value="Condomínio Solar")
        carregador = c.text_input("Carregador", value="EVSE-01")

        a, b, c = st.columns(3)
        usuario = a.text_input("Usuário", value="Novo usuário")
        unidade = b.text_input("Unidade ou centro de custo", value="Apto 101")
        veiculo = c.text_input("Veículo", value="Veículo elétrico")

        a, b, c = st.columns(3)
        placa = a.text_input("Placa", value="ABC1D23")
        data_inicio = b.date_input("Data de início", value=date.today())
        hora_inicio = c.time_input("Hora de início", value=time(18, 0))

        a, b, c = st.columns(3)
        data_fim = a.date_input("Data de fim", value=date.today())
        hora_fim = b.time_input("Hora de fim", value=time(20, 0))
        status = c.selectbox("Status", ["fechada", "pendente"])

        a, b, c, d, e = st.columns(5)
        kwh = a.number_input("Consumo (kWh)", min_value=0.0, value=12.0, step=0.1)
        tarifa = b.number_input("Tarifa (R$/kWh)", min_value=0.0, value=0.92, step=0.01)
        taxa_fixa = c.number_input("Taxa fixa (R$)", min_value=0.0, value=2.0, step=0.5)
        percentual = d.number_input(
            "Taxa operacional (decimal)",
            min_value=0.0,
            max_value=1.0,
            value=0.12,
            step=0.01,
            help="Use 0,12 para representar 12%.",
        )
        desconto = e.number_input("Desconto (R$)", min_value=0.0, value=0.0, step=0.5)

        enviado = st.form_submit_button("Calcular e registrar", type="primary")

    if enviado:
        inicio = datetime.combine(data_inicio, hora_inicio).isoformat(timespec="minutes")
        fim = (
            datetime.combine(data_fim, hora_fim).isoformat(timespec="minutes")
            if status == "fechada"
            else ""
        )
        try:
            sessao = processar_sessao(
                banco,
                {
                    "sessao_id": sessao_id,
                    "local": local,
                    "carregador": carregador,
                    "usuario": usuario,
                    "unidade": unidade,
                    "veiculo": veiculo,
                    "placa": placa,
                    "inicio": inicio,
                    "fim": fim,
                    "kwh_consumido": kwh,
                    "tarifa_kwh": tarifa,
                    "taxa_fixa": taxa_fixa,
                    "percentual_operacional": percentual,
                    "desconto": desconto,
                    "status": status,
                    "origem_dado": "manual",
                },
            )
            st.success(f"Sessão {sessao['sessao_id']} registrada.")
            st.write(sessao["memoria_calculo"])
            if sessao["ia_anomalia"]:
                st.warning("A IA pediu revisão: " + " ".join(sessao["ia_motivos"]))
            else:
                st.info("A análise automática classificou a sessão como normal.")
        except ValueError as erro:
            st.error(str(erro))


def pagina_importacao(banco: Banco) -> None:
    st.title("Importar sessões por CSV")
    st.write(
        "O arquivo pode vir de uma exportação ou de dados simulados. "
        "O sistema sempre recalcula o rateio e executa a análise de IA."
    )
    arquivo = st.file_uploader("Escolha um arquivo CSV", type=["csv"])
    if not arquivo:
        st.download_button(
            "Baixar CSV de exemplo",
            data=CSV_EXEMPLO.read_bytes(),
            file_name="exemplos-sessoes.csv",
            mime="text/csv",
        )
        return

    conteudo = arquivo.getvalue().decode("utf-8-sig")
    try:
        previa = pd.read_csv(io.StringIO(conteudo))
        st.dataframe(previa.head(10), width="stretch", hide_index=True)
    except Exception as erro:  # pandas fornece uma mensagem melhor para CSV quebrado
        st.error(f"Não foi possível ler o arquivo: {erro}")
        return

    substituir = st.checkbox("Atualizar sessões que já possuem o mesmo código")
    if st.button("Importar e analisar", type="primary"):
        resultado = importar_csv_texto(banco, conteudo, substituir=substituir)
        st.success(f"{len(resultado['importadas'])} sessão(ões) importadas.")
        if resultado["ignoradas"]:
            st.info(f"{len(resultado['ignoradas'])} sessão(ões) já existiam e foram ignoradas.")
        if resultado["erros"]:
            st.error("\n".join(resultado["erros"]))


def pagina_sessoes(banco: Banco) -> None:
    st.title("Sessões e rateio")
    sessoes = banco.listar_sessoes()
    if not sessoes:
        st.info("Nenhuma sessão cadastrada.")
        return

    locais = ["Todos"] + sorted({sessao["local"] for sessao in sessoes})
    filtro = st.selectbox("Filtrar por local", locais)
    filtradas = sessoes if filtro == "Todos" else [s for s in sessoes if s["local"] == filtro]
    st.dataframe(tabela_sessoes(filtradas), width="stretch", hide_index=True)

    st.download_button(
        "Exportar relatório CSV",
        data=gerar_csv_relatorio(filtradas).encode("utf-8-sig"),
        file_name="relatorio-ev-chargeops.csv",
        mime="text/csv",
    )

    st.subheader("Memória de cálculo")
    sessao_id = st.selectbox("Escolha uma sessão", [s["sessao_id"] for s in filtradas])
    sessao = banco.buscar_sessao(sessao_id)
    if not sessao:
        return

    a, b, c = st.columns(3)
    a.metric("Consumo", f"{sessao['kwh_consumido']:.2f} kWh")
    b.metric("Total", formatar_reais(sessao["valor_total"]))
    c.metric("Score da IA", f"{sessao['ia_score']:.1f}/100")
    st.markdown(f'<div class="ev-card">{sessao["memoria_calculo"]}</div>', unsafe_allow_html=True)

    if sessao["ia_anomalia"]:
        st.error("Revisão necessária: " + " ".join(sessao["ia_motivos"]))
    else:
        st.success("Sessão dentro do padrão conhecido.")
    st.caption("Método usado: " + sessao["ia_metodo"])


def pagina_ia(banco: Banco) -> None:
    st.title("Inteligência operacional")
    st.markdown(
        """
        <div class="ev-card">
        <h3>Como o módulo funciona</h3>
        Cada sessão vira quatro números: consumo, duração, potência média e horário de início.
        O detector KNN compara esses números com as sessões históricas mais próximas. Regras
        operacionais também identificam dados impossíveis, como potência acima do limite do
        carregador. A IA apenas pede revisão; ela nunca altera o valor cobrado.
        </div>
        """,
        unsafe_allow_html=True,
    )

    sessoes = banco.listar_sessoes()
    anomalias = [s for s in sessoes if s["ia_anomalia"]]
    st.subheader("Sessões sinalizadas")
    if anomalias:
        st.dataframe(tabela_sessoes(anomalias), width="stretch", hide_index=True)
        for sessao in anomalias:
            with st.expander(f"{sessao['sessao_id']} — {sessao['usuario']}"):
                st.write("Score:", sessao["ia_score"])
                st.write("Motivos:", " ".join(sessao["ia_motivos"]))
                st.write("Método:", sessao["ia_metodo"])
    else:
        st.info("Nenhuma sessão foi sinalizada.")

    st.subheader("Previsão simples para os próximos 7 dias")
    previsao = prever_demanda(sessoes)
    if previsao:
        dados = pd.DataFrame(previsao).set_index("data")
        st.line_chart(dados, y="kwh_previsto", color="#38bdf8")
        st.caption(
            "A projeção usa a média diária e o padrão disponível por dia da semana. "
            "Ela serve para planejamento, não para cobrança."
        )
    else:
        st.info("Ainda não há histórico suficiente para a previsão.")


def main() -> None:
    banco = iniciar_banco()
    st.sidebar.title("EV ChargeOps")
    st.sidebar.caption("Protótipo funcional — Sprint 2")
    pagina = st.sidebar.radio(
        "Navegação",
        [
            "Visão geral",
            "Nova sessão",
            "Importar CSV",
            "Sessões e rateio",
            "Módulo de IA",
        ],
    )
    st.sidebar.divider()
    st.sidebar.caption("GoodWe + FIAP — Enterprise Challenge 2026")

    if pagina == "Visão geral":
        pagina_visao_geral(banco)
    elif pagina == "Nova sessão":
        pagina_nova_sessao(banco)
    elif pagina == "Importar CSV":
        pagina_importacao(banco)
    elif pagina == "Sessões e rateio":
        pagina_sessoes(banco)
    else:
        pagina_ia(banco)


if __name__ == "__main__":
    main()
