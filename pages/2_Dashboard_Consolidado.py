import json

import streamlit as st
import pandas as pd

from database.consolidados_db import (
    init_consolidados_db,
    listar_consolidados,
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

if df_consolidados.empty:
    st.warning(
        "Nenhum consolidado salvo no histórico ainda. "
        "Gere um consolidado na página de Consolidação."
    )
    st.stop()

st.sidebar.header("🔎 Filtros")

# =========================
# Tratamento de ano/mês
# =========================

df_consolidados["ano"] = pd.to_numeric(df_consolidados["ano"], errors="coerce")
df_consolidados["mes"] = pd.to_numeric(df_consolidados["mes"], errors="coerce")

anos = sorted(df_consolidados["ano"].dropna().unique())

if not anos:
    st.error("Não há ano identificado nos consolidados salvos.")
    st.stop()

ano_sel = st.sidebar.selectbox(
    "Ano",
    anos,
    index=len(anos) - 1
)

df_ano = df_consolidados[df_consolidados["ano"] == ano_sel].copy()

meses = sorted(df_ano["mes"].dropna().unique())

if not meses:
    st.error("Não há mês identificado para o ano selecionado.")
    st.stop()

mes_sel = st.sidebar.selectbox(
    "Mês",
    meses,
    index=len(meses) - 1
)

df_mes = df_ano[df_ano["mes"] == mes_sel].copy()

if df_mes.empty:
    st.warning("Nenhum consolidado encontrado para os filtros selecionados.")
    st.stop()

opcoes_consolidados = [
    f'{row["nome_arquivo"]} — {row["data_geracao"]}'
    for _, row in df_mes.iterrows()
]

opcao_consolidado = st.sidebar.selectbox(
    "Consolidado",
    opcoes_consolidados
)

idx = opcoes_consolidados.index(opcao_consolidado)
consolidado_selecionado = df_mes.iloc[idx]
consolidado_id = consolidado_selecionado["consolidado_id"]

# =========================
# Resumo
# =========================

st.subheader("📌 Resumo do consolidado selecionado")

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

# =========================
# Download
# =========================

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

# =========================
# Histórico de consolidados
# =========================

st.subheader("📚 Histórico de consolidados salvos")

df_exibir = df_consolidados.copy()

colunas_exibir = [
    "nome_arquivo",
    "data_processada",
    "ano",
    "mes",
    "data_geracao",
]

colunas_exibir = [
    col for col in colunas_exibir
    if col in df_exibir.columns
]

st.dataframe(
    df_exibir[colunas_exibir],
    use_container_width=True
)

csv = df_exibir[colunas_exibir].to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "⬇️ Baixar histórico em CSV",
    data=csv,
    file_name="historico_consolidados.csv",
    mime="text/csv"
)

st.divider()

# =========================
# Logs e abas
# =========================

st.subheader("📝 Detalhes do consolidado")

col_log, col_abas = st.columns(2)

with col_log:
    st.markdown("### Logs")

    logs_raw = consolidado_selecionado.get("logs", "")

    try:
        logs = json.loads(logs_raw) if logs_raw else []
    except Exception:
        logs = []

    if logs:
        st.code("\n".join(logs), language="text")
    else:
        st.info("Nenhum log disponível para este consolidado.")

with col_abas:
    st.markdown("### Abas criadas")

    abas_raw = consolidado_selecionado.get("abas_criadas", "")

    try:
        abas = json.loads(abas_raw) if abas_raw else []
    except Exception:
        abas = []

    if abas:
        for aba in abas:
            st.write(f"- {aba}")
    else:
        st.info("Nenhuma aba registrada para este consolidado.")

st.divider()

# =========================
# Administração
# =========================

st.subheader("⚙️ Administração")

with st.expander("Excluir consolidado selecionado"):
    st.warning(
        "Atenção: essa ação remove o arquivo consolidado do histórico compartilhado."
    )

    if st.button("Excluir consolidado selecionado"):
        excluir_consolidado(consolidado_id)
        st.success("Consolidado excluído do histórico.")
        st.rerun()
