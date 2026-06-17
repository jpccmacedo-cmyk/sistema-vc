import streamlit as st
import pandas as pd

from database.consolidados_db import (
    init_consolidados_db,
    listar_consolidados,
    carregar_indicadores_consolidados,
    carregar_arquivo_consolidado,
    excluir_consolidado,
)


st.set_page_config(
    page_title="Dashboard Consolidado",
    page_icon="📊",
    layout="wide"
)

init_consolidados_db()

st.title("📊 Dashboard dos Consolidados")
st.caption("Histórico compartilhado dos arquivos consolidados gerados pelo sistema.")

df_consolidados = listar_consolidados()
df_indicadores = carregar_indicadores_consolidados()

if df_consolidados.empty:
    st.warning("Nenhum consolidado salvo no histórico ainda. Gere um consolidado na página de Consolidação.")
    st.stop()

st.sidebar.header("🔎 Filtros")

anos = sorted(df_consolidados["ano"].dropna().unique())

ano_sel = st.sidebar.selectbox(
    "Ano",
    anos,
    index=len(anos) - 1
)

df_cons_ano = df_consolidados[df_consolidados["ano"] == ano_sel].copy()

meses = sorted(df_cons_ano["mes"].dropna().unique())

mes_sel = st.sidebar.selectbox(
    "Mês",
    meses,
    index=len(meses) - 1
)

df_cons_mes = df_cons_ano[df_cons_ano["mes"] == mes_sel].copy()

opcoes_consolidados = [
    f'{row["nome_arquivo"]} — {row["data_geracao"]}'
    for _, row in df_cons_mes.iterrows()
]

opcao_consolidado = st.sidebar.selectbox(
    "Consolidado",
    opcoes_consolidados
)

idx = opcoes_consolidados.index(opcao_consolidado)
consolidado_selecionado = df_cons_mes.iloc[idx]
consolidado_id = consolidado_selecionado["consolidado_id"]

df_base = df_indicadores[
    df_indicadores["consolidado_id"] == consolidado_id
].copy()

st.subheader("📌 Resumo do consolidado")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Arquivo", consolidado_selecionado["nome_arquivo"])

with col2:
    st.metric("Data processada", str(consolidado_selecionado["data_processada"]))

with col3:
    st.metric("Ano", int(consolidado_selecionado["ano"]))

with col4:
    st.metric("Mês", int(consolidado_selecionado["mes"]))

st.divider()

st.subheader("📥 Download do consolidado")

nome_arquivo, arquivo_bytes = carregar_arquivo_consolidado(consolidado_id)

if arquivo_bytes:
    st.download_button(
        "⬇️ Baixar arquivo consolidado",
        data=arquivo_bytes,
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("Arquivo Excel não encontrado no banco.")

st.divider()

if df_base.empty:
    st.warning("Nenhum indicador foi extraído deste consolidado.")
    st.stop()

plantas = sorted(df_base["planta"].dropna().unique())
grupos = sorted(df_base["grupo"].dropna().unique())
indicadores = sorted(df_base["indicador"].dropna().unique())

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    filtro_plantas = st.multiselect(
        "Plantas",
        plantas,
        default=plantas
    )

with col_f2:
    filtro_grupos = st.multiselect(
        "Grupos",
        grupos,
        default=grupos
    )

with col_f3:
    filtro_indicadores = st.multiselect(
        "Indicadores",
        indicadores,
        default=indicadores
    )

df_filtrado = df_base[
    df_base["planta"].isin(filtro_plantas)
    & df_base["grupo"].isin(filtro_grupos)
    & df_base["indicador"].isin(filtro_indicadores)
].copy()

st.subheader("📊 Indicadores extraídos")

st.dataframe(
    df_filtrado,
    use_container_width=True
)

st.divider()

st.subheader("📈 Comparativo por planta")

df_grafico = df_filtrado.copy()
df_grafico["resultado"] = pd.to_numeric(df_grafico["resultado"], errors="coerce")
df_grafico = df_grafico.dropna(subset=["resultado"])

if df_grafico.empty:
    st.info("Não há valores numéricos suficientes para gerar gráfico.")
else:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        indicador_grafico = st.selectbox(
            "Indicador",
            sorted(df_grafico["indicador"].unique())
        )

    with col_g2:
        grupos_disponiveis = sorted(
            df_grafico[df_grafico["indicador"] == indicador_grafico]["grupo"].unique()
        )

        grupo_grafico = st.selectbox(
            "Grupo",
            grupos_disponiveis
        )

    df_plot = df_grafico[
        (df_grafico["indicador"] == indicador_grafico)
        & (df_grafico["grupo"] == grupo_grafico)
    ]

    tabela_plot = df_plot.pivot_table(
        index="planta",
        values="resultado",
        aggfunc="first"
    )

    st.bar_chart(tabela_plot)

st.divider()

st.subheader("📚 Histórico do indicador")

df_hist = df_indicadores.copy()
df_hist["resultado"] = pd.to_numeric(df_hist["resultado"], errors="coerce")
df_hist = df_hist.dropna(subset=["resultado"])

if df_hist.empty:
    st.info("Ainda não há histórico suficiente.")
else:
    col_h1, col_h2 = st.columns(2)

    with col_h1:
        indicador_hist = st.selectbox(
            "Indicador histórico",
            sorted(df_hist["indicador"].dropna().unique())
        )

    with col_h2:
        grupo_hist = st.selectbox(
            "Grupo histórico",
            sorted(df_hist[df_hist["indicador"] == indicador_hist]["grupo"].dropna().unique())
        )

    df_hist_filtrado = df_hist[
        (df_hist["indicador"] == indicador_hist)
        & (df_hist["grupo"] == grupo_hist)
    ].copy()

    df_hist_filtrado["periodo"] = (
        df_hist_filtrado["ano"].astype(str)
        + "-"
        + df_hist_filtrado["mes"].astype(str).str.zfill(2)
    )

    st.dataframe(
        df_hist_filtrado,
        use_container_width=True
    )

    grafico_hist = df_hist_filtrado.pivot_table(
        index="periodo",
        columns="planta",
        values="resultado",
        aggfunc="first"
    )

    st.line_chart(grafico_hist)

st.divider()

st.subheader("⚙️ Administração")

with st.expander("Excluir consolidado selecionado"):
    st.warning("Atenção: isso remove o arquivo e os indicadores deste consolidado do histórico.")

    if st.button("Excluir consolidado selecionado"):
        excluir_consolidado(consolidado_id)
        st.success("Consolidado excluído do histórico.")
        st.rerun()
