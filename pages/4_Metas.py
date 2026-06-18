import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd

from database.metas_db import (
    init_metas_db,
    normalizar_planilha_metas,
    salvar_metas_no_banco,
    carregar_metas,
    excluir_metas_ano,
)


st.set_page_config(
    page_title="Metas",
    page_icon="🎯",
    layout="wide"
)

init_metas_db()

st.title("🎯 Cadastro de Metas")
st.caption("Upload da planilha METAS 2026 CN.xlsx e gravação das metas no PostgreSQL.")

st.info(
    "A página lê a aba 'METAS 2026', aplica a regra de metas mensais/anuais, "
    "usa a aba 'TIPOS' para Maior/Menor Melhor e trata KKC como número sem %. "
)

st.sidebar.header("📤 Upload")

arquivo = st.sidebar.file_uploader(
    "Enviar planilha de metas",
    type=["xlsx", "xlsm"]
)

usuario = st.sidebar.text_input("Usuário / responsável", value="")

if st.sidebar.button("Processar e salvar metas", disabled=arquivo is None):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(arquivo.getvalue())
            caminho_temp = tmp.name

        df_metas = normalizar_planilha_metas(caminho_temp)

        if df_metas.empty:
            st.error("Nenhuma meta foi extraída da planilha.")
            st.stop()

        qtd = salvar_metas_no_banco(
            df_metas=df_metas,
            usuario_upload=usuario or None,
            arquivo_origem=arquivo.name
        )

        st.success(f"{qtd} meta(s) salva(s) com sucesso no PostgreSQL.")

        Path(caminho_temp).unlink(missing_ok=True)

        st.rerun()

    except Exception as e:
        st.error("Erro ao processar planilha de metas.")
        st.exception(e)

df = carregar_metas()

if df.empty:
    st.warning("Nenhuma meta cadastrada ainda.")
    st.stop()

st.subheader("📌 Resumo das metas cadastradas")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de metas", len(df))

with col2:
    st.metric("Anos", df["ano"].nunique())

with col3:
    st.metric("Códigos", df["codigo"].nunique())

with col4:
    st.metric("Indicadores", df["indicador"].nunique())

st.divider()

st.subheader("🔎 Filtros")

anos = sorted(df["ano"].dropna().unique())
codigos = sorted(df["codigo"].dropna().unique())
grupos = sorted(df["grupo"].dropna().unique())
indicadores = sorted(df["indicador"].dropna().unique())

colf1, colf2, colf3, colf4 = st.columns(4)

with colf1:
    filtro_anos = st.multiselect("Ano", anos, default=anos)

with colf2:
    filtro_codigos = st.multiselect("Código", codigos, default=codigos)

with colf3:
    filtro_grupos = st.multiselect("Grupo", grupos, default=grupos)

with colf4:
    filtro_indicadores = st.multiselect("Indicador", indicadores, default=indicadores)

df_filtrado = df[
    df["ano"].isin(filtro_anos)
    & df["codigo"].isin(filtro_codigos)
    & df["grupo"].isin(filtro_grupos)
    & df["indicador"].isin(filtro_indicadores)
].copy()

st.dataframe(df_filtrado, use_container_width=True)

csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "⬇️ Baixar metas filtradas em CSV",
    data=csv,
    file_name="metas_consolidados.csv",
    mime="text/csv"
)

st.divider()

st.subheader("⚙️ Administração")

with st.expander("Excluir metas por ano"):
    ano_excluir = st.selectbox("Ano para excluir", anos)

    st.warning(
        "Atenção: isso apaga todas as metas cadastradas para o ano selecionado."
    )

    if st.button("Excluir metas do ano selecionado"):
        excluir_metas_ano(ano_excluir)
        st.success(f"Metas do ano {ano_excluir} excluídas.")
        st.rerun()
