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

from core.stfd_dashboard import (
    montar_tabela_st,
    estilizar_st,
    montar_tabela_fd,
    estilizar_fd,
)


st.set_page_config(
    page_title="Dashboard ST & FD",
    page_icon="📈",
    layout="wide"
)

init_stfd_db()

st.title("📈 Dashboard ST & FD")
st.caption("Dashboard com histórico compartilhado em PostgreSQL, visual semelhante ao modelo em anexo.")

st.markdown("""
<div style="display:flex;gap:20px;margin:8px 0 16px 0;font-size:13px;">
  <div><span style="background:#C6EFCE;padding:3px 12px;border-radius:4px;"></span> Dentro da meta</div>
  <div><span style="background:#FFEB9C;padding:3px 12px;border-radius:4px;"></span> Parcial</div>
  <div><span style="background:#FFC7CE;padding:3px 12px;border-radius:4px;"></span> Fora da meta</div>
</div>
""", unsafe_allow_html=True)

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

            if df_records.empty:
                excluir_batch(batch_id)
                st.error("Nenhum registro foi extraído do arquivo.")

                if erros:
                    st.warning("Avisos encontrados:")
                    for erro in erros:
                        st.write(f"- {erro}")

                st.stop()

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

anos = sorted(df["ano"].dropna().unique())

ano_sel = st.sidebar.selectbox(
    "Ano",
    anos,
    index=len(anos) - 1
)

df_ano = df[df["ano"] == ano_sel].copy()

meses = sorted(df_ano["mes"].dropna().unique())

mes_sel = st.sidebar.selectbox(
    "Mês",
    meses,
    index=len(meses) - 1
)

df_mes = df_ano[df_ano["mes"] == mes_sel].copy()

plantas = sorted(df_mes["planta"].dropna().unique())

plantas_sel = st.sidebar.multiselect(
    "Plantas",
    plantas,
    default=plantas
)

df_mes = df_mes[df_mes["planta"].isin(plantas_sel)].copy()

st.subheader("📌 Resumo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Uploads salvos", df_uploads["batch_id"].nunique())

with col2:
    st.metric("Ano selecionado", int(ano_sel))

with col3:
    st.metric("Mês selecionado", int(mes_sel))

with col4:
    st.metric("Plantas", df_mes["planta"].nunique())

st.divider()

tab_st, tab_fd, tab_uploads, tab_base = st.tabs([
    "ST Heatmap",
    "FD Multiflex",
    "Histórico de uploads",
    "Base filtrada"
])


with tab_st:
    st.subheader(f"ST Heatmap — {int(mes_sel):02d}/{int(ano_sel)}")

    tabela_st = montar_tabela_st(df_mes)

    if tabela_st.empty:
        st.info("Nenhum dado ST para os filtros selecionados.")
    else:
        st.dataframe(
            estilizar_st(tabela_st),
            use_container_width=True,
            hide_index=True
        )


with tab_fd:
    st.subheader(f"FD Multiflex — {int(mes_sel):02d}/{int(ano_sel)}")

    tabela_fd = montar_tabela_fd(df_mes)

    if tabela_fd.empty:
        st.info("Nenhum dado FD para os filtros selecionados.")
    else:
        st.dataframe(
            estilizar_fd(tabela_fd),
            use_container_width=True,
            hide_index=True
        )


with tab_uploads:
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


with tab_base:
    st.subheader("Base filtrada")

    st.dataframe(df_mes, use_container_width=True)

    csv = df_mes.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "Baixar CSV filtrado",
        data=csv,
        file_name="historico_st_fd_filtrado.csv",
        mime="text/csv"
    )
