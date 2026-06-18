from io import BytesIO

import streamlit as st
import pandas as pd

from database.consolidados_db import (
    init_consolidados_db,
    listar_consolidados,
    carregar_arquivo_consolidado,
)

from database.metas_db import (
    init_metas_db,
    carregar_metas,
)

st.set_page_config(
    page_title="Dashboard Consolidado",
    page_icon=":bar_chart:",
    layout="wide"
)

st.title("Dashboard Consolidado")
st.caption("Pagina minima para validar consolidados, metas e banco de dados.")

try:
    init_consolidados_db()
    init_metas_db()
    df_consolidados = listar_consolidados()
    df_metas = carregar_metas()
except Exception as erro:
    st.error("Erro ao carregar dados do banco.")
    st.exception(erro)
    st.stop()

col1, col2 = st.columns(2)
col1.metric("Consolidados salvos", len(df_consolidados))
col2.metric("Metas cadastradas", len(df_metas))

st.divider()
st.subheader("Historico de consolidados")

if df_consolidados.empty:
    st.warning("Nenhum consolidado salvo ainda.")
    st.stop()

st.dataframe(df_consolidados, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Download de consolidado")

df_consolidados["ano"] = pd.to_numeric(df_consolidados["ano"], errors="coerce")
df_consolidados["mes"] = pd.to_numeric(df_consolidados["mes"], errors="coerce")

anos = sorted(df_consolidados["ano"].dropna().unique())
if not anos:
    st.warning("Nenhum ano identificado nos consolidados.")
    st.stop()

ano_sel = st.selectbox("Ano", anos, index=len(anos) - 1)
df_ano = df_consolidados[df_consolidados["ano"] == ano_sel].copy()

meses = sorted(df_ano["mes"].dropna().unique())
if not meses:
    st.warning("Nenhum mes identificado para o ano selecionado.")
    st.stop()

mes_sel = st.selectbox("Mes", meses, index=len(meses) - 1)
df_mes = df_ano[df_ano["mes"] == mes_sel].copy()

opcoes = []
for _, row in df_mes.iterrows():
    opcoes.append(str(row["nome_arquivo"]) + " - " + str(row["data_geracao"]))

if not opcoes:
    st.warning("Nenhum consolidado encontrado para os filtros selecionados.")
    st.stop()

opcao = st.selectbox("Consolidado", opcoes)
idx = opcoes.index(opcao)
consolidado = df_mes.iloc[idx]
consolidado_id = consolidado["consolidado_id"]

nome_arquivo, arquivo_bytes = carregar_arquivo_consolidado(consolidado_id)

if arquivo_bytes:
    st.download_button(
        "Baixar arquivo consolidado",
        data=arquivo_bytes,
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("Arquivo nao encontrado no banco.")

st.divider()
st.subheader("Metas cadastradas")

if df_metas.empty:
    st.warning("Nenhuma meta cadastrada ainda. Faca upload na pagina Metas.")
else:
    st.dataframe(df_metas, use_container_width=True, hide_index=True)
