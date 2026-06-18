from io import BytesIO
import json

import streamlit as st
import pandas as pd
from openpyxl import load_workbook

from database.consolidados_db import (
    init_consolidados_db,
    listar_consolidados,
    carregar_arquivo_consolidado,
    excluir_consolidado,
)

from database.metas_db import (
    init_metas_db,
    carregar_metas,
)

from utils.mapa_indicadores import extrair_resultados_consolidado


st.set_page_config(
    page_title="Dashboard Consolidado",
    page_icon="📊",
    layout="wide"
)

init_consolidados_db()
init_metas_db()

st.title("📊 Dashboard Consolidado com Farol")
st.caption("Histórico compartilhado dos consolidados, comparação com metas e farol.")

df_consolidados = listar_consolidados()
df_metas = carregar_metas()

if df_consolidados.empty:
    st.warning("Nenhum consolidado salvo ainda. Gere um consolidado na página de Consolidação.")
    st.stop()

if df_metas.empty:
    st.warning("Nenhuma meta cadastrada ainda. Faça upload da planilha na página Metas.")
    st.stop()


def ajustar_resultado_para_comparacao(indicador, valor):
    """
    KKC deve comparar na escala 0–100.
    Se resultado vier como 0,55, vira 55.
    """

    try:
        if pd.isna(valor):
            return None
    except Exception:
        pass

    if valor is None:
        return None

    try:
        valor = float(valor)
    except Exception:
        return None

    if indicador in ["%KKC", "KKC"] and abs(valor) <= 1:
        return valor * 100

    return valor


def buscar_meta(row, df_metas_periodo):
    ano = int(row["ano"])
    mes = int(row["mes"])
    codigo = row["planta"]
    grupo = row["grupo"]
    indicador = row["indicador"]

    # 1. Busca meta mensal
    mensal = df_metas_periodo[
        (df_metas_periodo["ano"] == ano)
        & (df_metas_periodo["mes"] == mes)
        & (df_metas_periodo["codigo"] == codigo)
        & (df_metas_periodo["grupo"] == grupo)
        & (df_metas_periodo["indicador"] == indicador)
    ]

    if not mensal.empty:
        return mensal.iloc[0]

    # 2. Busca meta anual
    anual = df_metas_periodo[
        (df_metas_periodo["ano"] == ano)
        & (df_metas_periodo["mes"] == 0)
        & (df_metas_periodo["codigo"] == codigo)
        & (df_metas_periodo["grupo"] == grupo)
        & (df_metas_periodo["indicador"] == indicador)
    ]

    if not anual.empty:
        return anual.iloc[0]

    return None


def calcular_status(resultado, meta, sentido):
    if resultado is None or pd.isna(resultado):
        return "sem_resultado"

    if meta is None or pd.isna(meta):
        return "sem_meta"

    if sentido == "informativo":
        return "informativo"

    if sentido == "menor":
        return "verde" if resultado <= meta else "vermelho"

    return "verde" if resultado >= meta else "vermelho"


def cor_farol(status):
    if status == "verde":
        return "background-color: #C6EFCE; color: #006100; font-weight: 700"

    if status == "vermelho":
        return "background-color: #FFC7CE; color: #9C0006; font-weight: 700"

    if status == "informativo":
        return "background-color: #E2E8F0; color: #334155"

    return "background-color: #FFFFFF"


def simbolo_farol(status):
    if status == "verde":
        return "🟢"

    if status == "vermelho":
        return "🔴"

    if status == "informativo":
        return "⚪"

    if status == "sem_meta":
        return "⚫"

    return ""


def montar_farol(df_resultados, df_metas, ano, mes):
    df = df_resultados.copy()

    df["ano"] = int(ano)
    df["mes"] = int(mes)

    df = df.rename(columns={
        "Planta": "planta",
        "Grupo": "grupo",
        "Indicador": "indicador",
        "Celula": "celula",
        "Resultado": "resultado_original",
    })

    df["resultado"] = df.apply(
        lambda row: ajustar_resultado_para_comparacao(
            row["indicador"],
            row["resultado_original"]
        ),
        axis=1
    )

    metas_periodo = df_metas[
        (df_metas["ano"] == int(ano))
        & (df_metas["codigo"] != "CN")
    ].copy()

    registros = []

    for _, row in df.iterrows():
        meta_row = buscar_meta(row, metas_periodo)

        if meta_row is None:
            meta = None
            sentido = None
            tipo = None
            nome = None
            periodicidade = None
        else:
            meta = meta_row["meta"]
            sentido = meta_row["sentido"]
            tipo = meta_row["tipo"]
            nome = meta_row["nome"]
            periodicidade = meta_row["periodicidade"]

        status = calcular_status(row["resultado"], meta, sentido)

        registros.append({
            "Ano": row["ano"],
            "Mes": row["mes"],
            "Planta": row["planta"],
            "Nome": nome,
            "Grupo": row["grupo"],
            "Indicador": row["indicador"],
            "Resultado": row["resultado"],
            "Meta": meta,
            "Sentido": sentido,
            "Periodicidade": periodicidade,
            "Status": status,
            "Farol": simbolo_farol(status),
        })

    return pd.DataFrame(registros)


def estilizar_farol(df):
    def aplicar(row):
        estilos = []

        for col in df.columns:
            if col in ["Status", "Farol", "Resultado", "Meta"]:
                estilos.append(cor_farol(row["Status"]))
            else:
                estilos.append("")

        return estilos

    return df.style.apply(aplicar, axis=1)


# ==============================
# Filtros do consolidado
# ==============================

st.sidebar.header("🔎 Filtros")

df_consolidados["ano"] = pd.to_numeric(df_consolidados["ano"], errors="coerce")
df_consolidados["mes"] = pd.to_numeric(df_consolidados["mes"], errors="coerce")

anos = sorted(df_consolidados["ano"].dropna().unique())

ano_sel = st.sidebar.selectbox(
    "Ano",
    anos,
    index=len(anos) - 1
)

df_ano = df_consolidados[df_consolidados["ano"] == ano_sel].copy()

meses = sorted(df_ano["mes"].dropna().unique())

mes_sel = st.sidebar.selectbox(
    "Mês",
    meses,
    index=len(meses) - 1
)

df_mes = df_ano[df_ano["mes"] == mes_sel].copy()

opcoes = [
    f'{row["nome_arquivo"]} — {row["data_geracao"]}'
    for _, row in df_mes.iterrows()
]

opcao = st.sidebar.selectbox("Consolidado", opcoes)

idx = opcoes.index(opcao)
consolidado = df_mes.iloc[idx]
consolidado_id = consolidado["consolidado_id"]

nome_arquivo, arquivo_bytes = carregar_arquivo_consolidado(consolidado_id)

if not arquivo_bytes:
    st.error("Arquivo consolidado não encontrado no banco.")
    st.stop()

wb = load_workbook(BytesIO(arquivo_bytes), data_only=True)
df_resultados = extrair_resultados_consolidado(wb)

if df_resultados.empty:
    st.warning("Nenhum indicador extraído do consolidado.")
    st.stop()

df_farol = montar_farol(
    df_resultados=df_resultados,
    df_metas=df_metas,
    ano=int(ano_sel),
    mes=int(mes_sel)
)

# ==============================
# Resumo
# ==============================

st.subheader("📌 Resumo")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Arquivo", nome_arquivo)
col2.metric("Ano", int(ano_sel))
col3.metric("Mês", int(mes_sel))
col4.metric("Indicadores com meta", int(df_farol["Meta"].notna().sum()))

st.download_button(
    "⬇️ Baixar arquivo consolidado",
    data=arquivo_bytes,
    file_name=nome_arquivo,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.divider()

# ==============================
# Filtros internos
# ==============================

plantas = sorted(df_farol["Planta"].dropna().unique())
grupos = sorted(df_farol["Grupo"].dropna().unique())
indicadores = sorted(df_farol["Indicador"].dropna().unique())

colf1, colf2, colf3 = st.columns(3)

with colf1:
    filtro_plantas = st.multiselect("Plantas", plantas, default=plantas)

with colf2:
    filtro_grupos = st.multiselect("Grupos", grupos, default=grupos)

with colf3:
    filtro_indicadores = st.multiselect("Indicadores", indicadores, default=indicadores)

df_view = df_farol[
    df_farol["Planta"].isin(filtro_plantas)
    & df_farol["Grupo"].isin(filtro_grupos)
    & df_farol["Indicador"].isin(filtro_indicadores)
].copy()

# ==============================
# Farol
# ==============================

st.subheader("🚦 Farol dos Indicadores")

st.markdown("""
<div style="display:flex;gap:20px;margin:8px 0 16px 0;font-size:13px;">
  <div>🟢 Dentro da meta</div>
  <div>🔴 Fora da meta</div>
  <div>⚪ Informativo</div>
  <div>⚫ Sem meta</div>
</div>
""", unsafe_allow_html=True)

st.dataframe(
    estilizar_farol(df_view),
    use_container_width=True,
    hide_index=True
)

csv = df_view.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "⬇️ Baixar farol em CSV",
    data=csv,
    file_name="farol_consolidado.csv",
    mime="text/csv"
)

st.divider()

# ==============================
# Gráficos
# ==============================

st.subheader("📈 Gráficos")

df_num = df_view.dropna(subset=["Resultado"]).copy()

if df_num.empty:
    st.info("Não há dados numéricos suficientes para gráfico.")
else:
    colg1, colg2 = st.columns(2)

    with colg1:
        indicador_grafico = st.selectbox(
            "Indicador do gráfico",
            sorted(df_num["Indicador"].unique())
        )

    with colg2:
        grupo_grafico = st.selectbox(
            "Grupo do gráfico",
            sorted(df_num[df_num["Indicador"] == indicador_grafico]["Grupo"].unique())
        )

    df_grafico = df_num[
        (df_num["Indicador"] == indicador_grafico)
        & (df_num["Grupo"] == grupo_grafico)
    ].copy()

    tabela_grafico = df_grafico.pivot_table(
        index="Planta",
        values=["Resultado", "Meta"],
        aggfunc="first"
    )

    st.bar_chart(tabela_grafico)

st.divider()

# ==============================
# Histórico salvo
# ==============================

st.subheader("📚 Histórico de consolidados")

st.dataframe(
    df_consolidados[
        ["nome_arquivo", "data_processada", "ano", "mes", "data_geracao"]
    ],
    use_container_width=True
)

st.divider()

# ==============================
# Administração
# ==============================

with st.expander("⚙️ Excluir consolidado selecionado"):
    st.warning("Essa ação remove o consolidado do histórico compartilhado.")

    if st.button("Excluir consolidado selecionado"):
        excluir_consolidado(consolidado_id)
        st.success("Consolidado excluído.")
        st.rerun()
