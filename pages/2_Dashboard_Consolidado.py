from io import BytesIOfrom io import Bytes st
import pandas as pd
from openpyxl import load_workbook

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
    page_icon="📊",
    layout="wide"
)

st.title("Dashboard Consolidado")
st.caption("Teste seguro do Dashboard Consolidado com banco, consolidados e metas.")

try:
    init_consolidados_db()
    init_metas_db()

    df_consolidados = listar_consolidados()
    df_metas = carregar_metas()

except Exception as erro:
    st.error("Erro ao conectar no banco ou carregar tabelas.")
    st.exception(erro)
    st.stop()


st.subheader("Status das bases")

col1, col2 = st.columns(2)

with col1:
    st.metric("Consolidados salvos", len(df_consolidados))

with col2:
    st.metric("Metas cadastradas", len(df_metas))


if df_consolidados.empty:
    st.warning("Nenhum consolidado salvo ainda.")
    st.stop()


st.divider()

st.subheader("Historico de consolidados")

st.dataframe(
    df_consolidados,
    use_container_width=True,
    hide_index=True
)


st.divider()

st.subheader("Download de consolidado")

df_consolidados["ano"] = pd.to_numeric(df_consolidados["ano"], errors="coerce")
df_consolidados["mes"] = pd.to_numeric(df_consolidados["mes"], errors="coerce")

anos = sorted(df_consolidados["ano"].dropna().unique())

ano_sel = st.selectbox(
    "Ano",
    anos,
    index=len(anos) - 1
)

df_ano = df_consolidados[df_consolidados["ano"] == ano_sel].copy()

meses = sorted(df_ano["mes"].dropna().unique())

mes_sel = st.selectbox(
    "Mes",
    meses,
    index=len(meses) - 1
)

df_mes = df_ano[df_ano["mes"] == mes_sel].copy()

opcoes = [
    f'{row["nome_arquivo"]} - {row["data_geracao"]}'
    for _, row in df_mes.iterrows()
]

opcao = st.selectbox(
    "Consolidado",
    opcoes
)

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
    st.warning("Nenhuma meta cadastrada ainda. Faça upload na pagina Metas.")
else:
    st.dataframe(
        df_metas,
        use_container_width=True,
        hide_index=True
    )

