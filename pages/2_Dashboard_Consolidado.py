import streamlit as st
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook

from utils.historico import (
    carregar_historico_consolidados,
    remover_registro_historico
)

from utils.mapa_indicadores import extrair_resultados_consolidado


st.set_page_config(
    page_title="Dashboard Consolidado",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard dos Consolidados")
st.caption("Indicadores extraídos automaticamente dos arquivos consolidados salvos no histórico.")

historico = carregar_historico_consolidados()

if not historico:
    st.warning("Nenhum consolidado encontrado. Gere ou registre um consolidado na página de Consolidação.")

    st.page_link(
        "pages/1_Consolidacao.py",
        label="Ir para Consolidação",
        icon="📁"
    )

    st.stop()

historico = sorted(
    historico,
    key=lambda x: x.get("data_geracao", ""),
    reverse=True
)

st.sidebar.header("Filtros")

opcoes = [
    f'{item["nome_arquivo"]} — {item["data_geracao"]}'
    for item in historico
]

opcao_escolhida = st.sidebar.selectbox(
    "Selecione o consolidado",
    opcoes
)

item = historico[opcoes.index(opcao_escolhida)]
caminho_consolidado = Path(item["caminho"])

if not caminho_consolidado.exists():
    st.error("O arquivo consolidado registrado no histórico não foi encontrado.")

    if st.button("Remover registro quebrado do histórico"):
        remover_registro_historico(item["nome_arquivo"])
        st.rerun()

    st.stop()

wb = load_workbook(caminho_consolidado, data_only=True)

df_resultados = extrair_resultados_consolidado(wb)

if df_resultados.empty:
    st.warning(
        "Nenhum indicador foi extraído. "
        "Verifique se o consolidado tem as abas COB, CUI, EDE, NOB, PVE, SOB e XAM."
    )
    st.stop()

plantas = sorted(df_resultados["Planta"].dropna().unique())
grupos = sorted(df_resultados["Grupo"].dropna().unique())
indicadores = sorted(df_resultados["Indicador"].dropna().unique())

filtro_plantas = st.sidebar.multiselect(
    "Plantas",
    plantas,
    default=plantas
)

filtro_grupos = st.sidebar.multiselect(
    "Grupos",
    grupos,
    default=grupos
)

filtro_indicadores = st.sidebar.multiselect(
    "Indicadores",
    indicadores,
    default=indicadores
)

mostrar_vazios = st.sidebar.checkbox(
    "Mostrar indicadores sem valor",
    value=True
)

mask = (
    df_resultados["Planta"].isin(filtro_plantas)
    & df_resultados["Grupo"].isin(filtro_grupos)
    & df_resultados["Indicador"].isin(filtro_indicadores)
)

df_filtrado = df_resultados[mask].copy()

if not mostrar_vazios:
    df_filtrado = df_filtrado[df_filtrado["Resultado"].notna()]

st.subheader("📌 Resumo do consolidado")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Arquivo", item["nome_arquivo"])

with col2:
    st.metric("Data geração", item["data_geracao"])

with col3:
    st.metric("Plantas", df_filtrado["Planta"].nunique())

with col4:
    st.metric("Indicadores preenchidos", int(df_filtrado["Resultado"].notna().sum()))

st.divider()

st.subheader("📊 Indicadores extraídos")

st.dataframe(
    df_filtrado,
    use_container_width=True
)

csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "⬇️ Baixar indicadores filtrados em CSV",
    data=csv,
    file_name="indicadores_consolidado.csv",
    mime="text/csv"
)

st.divider()

st.subheader("📈 Comparativo por planta")

df_grafico = df_filtrado.dropna(subset=["Resultado"]).copy()
df_grafico["Resultado"] = pd.to_numeric(df_grafico["Resultado"], errors="coerce")
df_grafico = df_grafico.dropna(subset=["Resultado"])

if df_grafico.empty:
    st.info("Não há valores numéricos suficientes para gerar gráfico.")
else:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        indicador_grafico = st.selectbox(
            "Indicador",
            sorted(df_grafico["Indicador"].unique())
        )

    with col_g2:
        grupos_disponiveis = sorted(
            df_grafico[df_grafico["Indicador"] == indicador_grafico]["Grupo"].unique()
        )

        grupo_grafico = st.selectbox(
            "Grupo",
            grupos_disponiveis
        )

    df_ind = df_grafico[
        (df_grafico["Indicador"] == indicador_grafico)
        & (df_grafico["Grupo"] == grupo_grafico)
    ]

    tabela_grafico = df_ind.pivot_table(
        index="Planta",
        values="Resultado",
        aggfunc="first"
    )

    st.bar_chart(tabela_grafico)

st.divider()

st.subheader("📚 Histórico dos indicadores")


def montar_historico_indicadores(historico_lista):
    todos = []

    for reg in historico_lista:
        caminho = Path(reg["caminho"])

        if not caminho.exists():
            continue

        wb_hist = load_workbook(caminho, data_only=True)

        df = extrair_resultados_consolidado(wb_hist)

        if df.empty:
            continue

        df["Arquivo"] = reg["nome_arquivo"]
        df["Data geração"] = reg["data_geracao"]

        todos.append(df)

    if not todos:
        return pd.DataFrame()

    return pd.concat(todos, ignore_index=True)


df_historico = montar_historico_indicadores(historico)

if df_historico.empty:
    st.info("Ainda não há histórico suficiente.")
else:
    df_historico["Resultado"] = pd.to_numeric(
        df_historico["Resultado"],
        errors="coerce"
    )

    df_hist_num = df_historico.dropna(subset=["Resultado"])

    if df_hist_num.empty:
        st.info("O histórico ainda não possui valores numéricos suficientes.")
    else:
        col_h1, col_h2 = st.columns(2)

        with col_h1:
            indicador_hist = st.selectbox(
                "Indicador do histórico",
                sorted(df_hist_num["Indicador"].unique())
            )

        with col_h2:
            grupos_hist = sorted(
                df_hist_num[df_hist_num["Indicador"] == indicador_hist]["Grupo"].unique()
            )

            grupo_hist = st.selectbox(
                "Grupo do histórico",
                grupos_hist
            )

        df_hist_filtrado = df_hist_num[
            (df_hist_num["Indicador"] == indicador_hist)
            & (df_hist_num["Grupo"] == grupo_hist)
        ].copy()

        st.dataframe(
            df_hist_filtrado,
            use_container_width=True
        )

        grafico_historico = df_hist_filtrado.pivot_table(
            index="Data geração",
            columns="Planta",
            values="Resultado",
            aggfunc="first"
        )

        st.line_chart(grafico_historico)
