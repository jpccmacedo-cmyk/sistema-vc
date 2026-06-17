import streamlit as st
import pandas as pd

from database.stfd_db import (
    init_stfd_db,
    criar_batch_upload,
    salvar_records_stfd,
    listar_uploads,
    carregar_records,
    excluir_batch,
)

from core.stfd_parser import parse_st_fd_excel


st.set_page_config(
    page_title="Dashboard ST & FD",
    page_icon="📈",
    layout="wide"
)

init_stfd_db()

st.title("📈 Dashboard ST & FD")
st.caption("Histórico compartilhado em banco de dados. Todos os usuários veem os uploads salvos.")

st.sidebar.header("⚙️ Ações")

with st.sidebar.expander("📤 Enviar novo Excel", expanded=True):
    arquivo = st.file_uploader(
        "Excel com abas Diário - ST e Diário - FD Multiflex",
        type=["xlsx", "xlsm"]
    )

    usuario = st.text_input("Usuário / responsável", value="")
    observacao = st.text_area("Observação", value="")

    if st.button("Salvar upload no histórico", disabled=arquivo is None):
        try:
            file_bytes = arquivo.getvalue()

            batch_id, data_upload = criar_batch_upload(
                nome_arquivo=arquivo.name,
                usuario=usuario or None,
                observacao=observacao or None
            )

            df_records, erros = parse_st_fd_excel(
                file_bytes=file_bytes,
                batch_id=batch_id,
                data_upload=data_upload
            )

            qtd = salvar_records_stfd(df_records)

            st.success(f"Upload salvo com sucesso. {qtd} registro(s) gravado(s).")

            if erros:
                st.warning("Avisos encontrados:")

                for erro in erros:
                    st.write(f"- {erro}")

            st.rerun()

        except Exception as e:
            st.error(f"Erro ao salvar upload: {e}")


df_uploads = listar_uploads()
df = carregar_records()

if df.empty:
    st.info("Nenhum dado ST/FD salvo ainda. Envie um Excel no menu lateral.")
    st.stop()

st.sidebar.header("🔎 Filtros")

fontes = sorted(df["fonte"].dropna().unique())
anos = sorted(df["ano"].dropna().unique())
meses = sorted(df["mes"].dropna().unique())
plantas = sorted(df["planta"].dropna().unique())
kpis = sorted(df["kpi"].dropna().unique())

filtro_fontes = st.sidebar.multiselect(
    "Fonte",
    fontes,
    default=fontes
)

filtro_anos = st.sidebar.multiselect(
    "Ano",
    anos,
    default=anos
)

filtro_meses = st.sidebar.multiselect(
    "Mês",
    meses,
    default=meses
)

filtro_plantas = st.sidebar.multiselect(
    "Plantas",
    plantas,
    default=plantas
)

filtro_kpis = st.sidebar.multiselect(
    "KPI",
    kpis,
    default=kpis
)

df_filtrado = df[
    df["fonte"].isin(filtro_fontes)
    & df["ano"].isin(filtro_anos)
    & df["mes"].isin(filtro_meses)
    & df["planta"].isin(filtro_plantas)
    & df["kpi"].isin(filtro_kpis)
].copy()

st.subheader("📌 Resumo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Uploads salvos", df_uploads["batch_id"].nunique())

with col2:
    st.metric("Registros filtrados", len(df_filtrado))

with col3:
    st.metric("Plantas", df_filtrado["planta"].nunique())

with col4:
    st.metric("Meses no histórico", df_filtrado[["ano", "mes"]].drop_duplicates().shape[0])

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "ST",
    "FD",
    "Histórico de uploads",
    "Base filtrada"
])


with tab1:
    st.subheader("ST — Histórico diário")

    df_st = df_filtrado[df_filtrado["fonte"] == "ST"].copy()

    if df_st.empty:
        st.info("Nenhum dado ST nos filtros selecionados.")
    else:
        df_st["valor_real"] = pd.to_numeric(df_st["valor_real"], errors="coerce")
        df_st["m300"] = pd.to_numeric(df_st["m300"], errors="coerce")
        df_st["rf"] = pd.to_numeric(df_st["rf"], errors="coerce")

        planta_st = st.selectbox(
            "Planta ST",
            sorted(df_st["planta"].dropna().unique())
        )

        df_st_planta = df_st[df_st["planta"] == planta_st].copy()

        tabela = df_st_planta.pivot_table(
            index=["ano", "mes", "dia", "data_label"],
            values=["valor_real", "m300", "rf"],
            aggfunc="first"
        ).reset_index()

        st.dataframe(tabela, use_container_width=True)

        grafico = tabela.set_index("data_label")[["valor_real", "m300", "rf"]]
        st.line_chart(grafico)


with tab2:
    st.subheader("FD — Histórico diário")

    df_fd = df_filtrado[df_filtrado["fonte"] == "FD"].copy()

    if df_fd.empty:
        st.info("Nenhum dado FD nos filtros selecionados.")
    else:
        df_fd["valor_real"] = pd.to_numeric(df_fd["valor_real"], errors="coerce")

        planta_fd = st.selectbox(
            "Planta FD",
            sorted(df_fd["planta"].dropna().unique())
        )

        df_fd_planta = df_fd[df_fd["planta"] == planta_fd].copy()

        tabela_fd = df_fd_planta.pivot_table(
            index=["ano", "mes", "dia", "data_label"],
            columns="kpi",
            values="valor_real",
            aggfunc="first"
        ).reset_index()

        st.dataframe(tabela_fd, use_container_width=True)

        grafico_fd = tabela_fd.set_index("data_label").drop(
            columns=["ano", "mes", "dia"],
            errors="ignore"
        )

        st.line_chart(grafico_fd)


with tab3:
    st.subheader("Histórico de uploads")

    st.dataframe(df_uploads, use_container_width=True)

    if not df_uploads.empty:
        opcoes_excluir = [
            f'{row["nome_arquivo"]} — {row["data_upload"]}'
            for _, row in df_uploads.iterrows()
        ]

        opcao = st.selectbox(
            "Selecionar upload para excluir",
            opcoes_excluir
        )

        idx = opcoes_excluir.index(opcao)
        batch_id_excluir = df_uploads.iloc[idx]["batch_id"]

        if st.button("Excluir upload selecionado"):
            excluir_batch(batch_id_excluir)
            st.success("Upload excluído com sucesso.")
            st.rerun()


with tab4:
    st.subheader("Base filtrada")

    st.dataframe(df_filtrado, use_container_width=True)

    csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "Baixar CSV filtrado",
        data=csv,
        file_name="historico_st_fd_filtrado.csv",
        mime="text/csv"
    )
