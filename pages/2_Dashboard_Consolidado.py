from io import BytesIO

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook

from database.consolidados_db import (
    init_consolidados_db,
    listar_consolidados,
    carregar_arquivo_consolidado,
    excluir_consolidado,
)
from database.metas_db import init_metas_db, carregar_metas
from utils.mapa_indicadores import extrair_resultados_consolidado

st.set_page_config(
    page_title="Dashboard Consolidado",
    page_icon=":bar_chart:",
    layout="wide"
)

PLANTAS_ORDEM = [
    ("COB", "Corumba"),
    ("CUI", "Cuiaba"),
    ("EDE", "Edealina"),
    ("NOB", "Nobres"),
    ("PVE", "Porto Velho"),
    ("SOB", "Sobradinho"),
    ("XAM", "Xambioa"),
    ("CN", "Regional CN"),
]

PLANTAS_STATUS = ["COB", "CUI", "EDE", "NOB", "PVE", "SOB", "XAM"]

GRUPOS_ORDEM = [
    "Fornos",
    "Moagens Cru",
    "Moagens Cimento",
    "Ensacadeiras",
    "Britagens",
    "Estoques",
    "Volumes",
]

INDICADORES_ORDEM = {
    "Fornos": ["OEE", "FP", "FF", "MTBF", "%ST", "CT"],
    "Moagens Cru": ["OEE", "FP", "FF", "MTBF"],
    "Moagens Cimento": ["OEE", "FP", "FF", "MTBF", "%KKC"],
    "Ensacadeiras": ["OEE"],
    "Britagens": ["OEE"],
    "Estoques": ["Clinquer", "Clínquer", "Granel", "Ensacado", "Argamassa"],
    "Volumes": ["Cimento", "Clinquer", "Clínquer"],
}


def to_float(valor):
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except Exception:
        pass
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        texto = valor.strip()
        if texto.upper() in ["", "-", "NA", "N/A", "NAO TEM", "NÃO TEM"]:
            return None
        texto = texto.replace("%", "").replace(".", "").replace(",", ".")
        try:
            return float(texto)
        except Exception:
            return None
    return None


def ajustar_resultado(indicador, valor):
    numero = to_float(valor)
    if numero is None:
        return None
    if indicador in ["%KKC", "KKC"] and abs(numero) <= 1:
        return numero * 100
    return numero


def formatar_numero(valor, tipo=None):
    numero = to_float(valor)
    if numero is None:
        return "NA"
    if tipo == "inteiro":
        return f"{numero:,.0f}".replace(",", ".")
    return f"{numero:.1f}".replace(".", ",")
    
def formatar_data_farol(consolidado, ano, mes):
    try:
        data_processada = consolidado.get("data_processada")

        if data_processada is not None:
            data = pd.to_datetime(data_processada, errors="coerce")

            if pd.notna(data):
                return data.strftime("%d/%m/%Y")
    except Exception:
        pass

    return

def calcular_status(resultado, meta, sentido):
    if resultado is None:
        return "sem_resultado"
    if meta is None:
        return "sem_meta"
    if sentido == "informativo":
        return "informativo"
    if sentido == "menor":
        return "verde" if resultado <= meta else "vermelho"
    return "verde" if resultado >= meta else "vermelho"


def cor_status(status):
    if status == "verde":
        return "background-color: #00B050; color: white; font-weight: 700"
    if status == "vermelho":
        return "background-color: #FF0000; color: white; font-weight: 700"
    if status == "informativo":
        return "background-color: #D9D9D9; color: black; font-weight: 600"
    if status == "sem_meta":
        return "background-color: #F3F4F6; color: #6B7280"
    return "background-color: #CFCFCF; color: black; font-weight: 600"


def preparar_metas(df_metas):
    df = df_metas.copy()
    for col in ["ano", "mes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["meta"] = pd.to_numeric(df["meta"], errors="coerce")
    for col in ["codigo", "grupo", "indicador", "sentido", "tipo", "nome", "periodicidade"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df


def buscar_meta(df_metas, ano, mes, codigo, grupo, indicador):
    if df_metas.empty:
        return None
    mensal = df_metas[
        (df_metas["ano"] == int(ano))
        & (df_metas["mes"] == int(mes))
        & (df_metas["codigo"] == codigo)
        & (df_metas["grupo"] == grupo)
        & (df_metas["indicador"] == indicador)
    ]
    if not mensal.empty:
        return mensal.iloc[0]
    anual = df_metas[
        (df_metas["ano"] == int(ano))
        & (df_metas["mes"] == 0)
        & (df_metas["codigo"] == codigo)
        & (df_metas["grupo"] == grupo)
        & (df_metas["indicador"] == indicador)
    ]
    if not anual.empty:
        return anual.iloc[0]
    return None


def montar_base_farol(df_resultados, df_metas, ano, mes):
    df = df_resultados.copy()
    df = df.rename(columns={
        "Planta": "codigo",
        "Grupo": "grupo",
        "Indicador": "indicador",
        "Resultado": "resultado_original",
        "Celula": "celula",
    })
    registros = []
    for _, row in df.iterrows():
        codigo = row["codigo"]
        grupo = row["grupo"]
        indicador = row["indicador"]
        resultado = ajustar_resultado(indicador, row.get("resultado_original"))
        meta_row = buscar_meta(df_metas, ano, mes, codigo, grupo, indicador)
        if meta_row is None:
            meta = None
            sentido = None
            tipo = None
            nome = dict(PLANTAS_ORDEM).get(codigo, codigo)
            periodicidade = None
        else:
            meta = to_float(meta_row.get("meta"))
            sentido = meta_row.get("sentido")
            tipo = meta_row.get("tipo")
            nome = meta_row.get("nome")
            periodicidade = meta_row.get("periodicidade")
        status = calcular_status(resultado, meta, sentido)
        registros.append({
            "Ano": int(ano),
            "Mes": int(mes),
            "Codigo": codigo,
            "Nome": nome,
            "Grupo": grupo,
            "Indicador": indicador,
            "Resultado": resultado,
            "Meta": meta,
            "Sentido": sentido,
            "Tipo": tipo,
            "Periodicidade": periodicidade,
            "Status": status,
        })
    return pd.DataFrame(registros)


def pares_grupo_indicador(df_farol, df_metas, ano, mes):
    pares = set()
    for _, row in df_farol.iterrows():
        pares.add((row["Grupo"], row["Indicador"]))
    metas_cn = df_metas[
        (df_metas["ano"] == int(ano))
        & (df_metas["codigo"] == "CN")
        & (df_metas["mes"].isin([0, int(mes)]))
    ]
    for _, row in metas_cn.iterrows():
        pares.add((row["grupo"], row["indicador"]))

    def chave_ordem(par):
        grupo, indicador = par
        grupo_idx = GRUPOS_ORDEM.index(grupo) if grupo in GRUPOS_ORDEM else 99
        lista_ind = INDICADORES_ORDEM.get(grupo, [])
        ind_idx = lista_ind.index(indicador) if indicador in lista_ind else 99
        return grupo_idx, ind_idx, grupo, indicador

    return sorted(pares, key=chave_ordem)


def montar_tabela_farol(df_farol, df_metas, ano, mes):
    pares = pares_grupo_indicador(df_farol, df_metas, ano, mes)
    linhas = []
    status_celulas = {}
    grupo_anterior = None
    for idx, (grupo, indicador) in enumerate(pares):
        linha = {
            ("", "Grupo"): grupo if grupo != grupo_anterior else "",
            ("", "Indicador"): indicador,
        }
        grupo_anterior = grupo
        for codigo, nome_planta in PLANTAS_ORDEM:
            meta_row = buscar_meta(df_metas, ano, mes, codigo, grupo, indicador)
            if meta_row is None:
                meta = None
                tipo = None
            else:
                meta = to_float(meta_row.get("meta"))
                tipo = meta_row.get("tipo")
            if codigo == "CN":
                resultado = None
                status = "sem_resultado"
            else:
                resultado_row = df_farol[
                    (df_farol["Codigo"] == codigo)
                    & (df_farol["Grupo"] == grupo)
                    & (df_farol["Indicador"] == indicador)
                ]
                if resultado_row.empty:
                    resultado = None
                    status = "sem_resultado"
                else:
                    resultado = resultado_row.iloc[0]["Resultado"]
                    status = resultado_row.iloc[0]["Status"]
                    tipo = resultado_row.iloc[0].get("Tipo", tipo)
            linha[(nome_planta, "Meta")] = formatar_numero(meta, tipo)
            linha[(nome_planta, "MTD")] = formatar_numero(resultado, tipo)
            status_celulas[(idx, nome_planta)] = status
        linhas.append(linha)
    df_tabela = pd.DataFrame(linhas)
    df_tabela.columns = pd.MultiIndex.from_tuples(df_tabela.columns)
    return df_tabela, status_celulas


def estilizar_tabela_farol(df_tabela, status_celulas):
    def aplicar(row):
        estilos = []
        for col in df_tabela.columns:
            if col[1] == "MTD":
                status = status_celulas.get((row.name, col[0]), "sem_resultado")
                estilos.append(cor_status(status))
            elif col[1] == "Meta":
                estilos.append("background-color: #FFFFFF; color: black")
            elif col[1] == "Grupo":
                estilos.append("background-color: #BFBFBF; color: black; font-weight: 700")
            elif col[1] == "Indicador":
                estilos.append("background-color: #F8F8F8; color: black; font-weight: 600")
            else:
                estilos.append("")
        return estilos
    return df_tabela.style.apply(aplicar, axis=1)


def calcular_status_por_planta(df_farol):
    df = df_farol[
        df_farol["Codigo"].isin(PLANTAS_STATUS)
        & df_farol["Status"].isin(["verde", "vermelho"])
    ].copy()
    if df.empty:
        return pd.DataFrame()
    resumo = df.groupby(["Codigo", "Status"]).size().unstack(fill_value=0).reset_index()
    if "verde" not in resumo.columns:
        resumo["verde"] = 0
    if "vermelho" not in resumo.columns:
        resumo["vermelho"] = 0
    resumo["total"] = resumo["verde"] + resumo["vermelho"]
    resumo["Acima Meta MTD"] = resumo["verde"] / resumo["total"] * 100
    resumo["Abaixo Meta MTD"] = resumo["vermelho"] / resumo["total"] * 100
    resumo["Nome"] = resumo["Codigo"].map(dict(PLANTAS_ORDEM))
    resumo = resumo.sort_values("Acima Meta MTD", ascending=True)
    return resumo


def plot_status_mtd(df_status):
    fig, ax = plt.subplots(figsize=(8, 5))
    y = range(len(df_status))
    acima = df_status["Acima Meta MTD"]
    abaixo = df_status["Abaixo Meta MTD"]
    labels = df_status["Codigo"]
    ax.barh(y, acima, color="#109618", label="Acima Meta MTD")
    ax.barh(y, abaixo, left=acima, color="#D64550", label="Abaixo Meta MTD")
    for i, (a, b) in enumerate(zip(acima, abaixo)):
        if a > 5:
            ax.text(a / 2, i, f"{a:.2f}%".replace(".", ","), va="center", ha="center", color="white", fontsize=9)
        if b > 5:
            ax.text(a + b / 2, i, f"{b:.2f}%".replace(".", ","), va="center", ha="center", color="white", fontsize=9)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 100)
    ax.set_xlabel("")
    ax.set_title("Status Indicador (MTD)", fontsize=14, fontweight="bold", color="#1A2A8F")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=2, frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    return fig


init_consolidados_db()
init_metas_db()

st.title("Dashboard Consolidado com Farol")
st.caption("Farol mensal por planta, status MTD e historico compartilhado.")

try:
    df_consolidados = listar_consolidados()
    df_metas = preparar_metas(carregar_metas())
except Exception as e:
    st.error("Erro ao carregar dados do banco.")
    st.exception(e)
    st.stop()

if df_consolidados.empty:
    st.warning("Nenhum consolidado salvo ainda. Gere um consolidado na pagina de Consolidacao.")
    st.stop()

if df_metas.empty:
    st.warning("Nenhuma meta cadastrada ainda. Faca upload da planilha na pagina Metas.")
    st.stop()

st.sidebar.header("Filtros")
df_consolidados["ano"] = pd.to_numeric(df_consolidados["ano"], errors="coerce")
df_consolidados["mes"] = pd.to_numeric(df_consolidados["mes"], errors="coerce")
anos = sorted(df_consolidados["ano"].dropna().unique())
ano_sel = st.sidebar.selectbox("Ano", anos, index=len(anos) - 1)
df_ano = df_consolidados[df_consolidados["ano"] == ano_sel].copy()
meses = sorted(df_ano["mes"].dropna().unique())
mes_sel = st.sidebar.selectbox("Mes", meses, index=len(meses) - 1)
df_mes = df_ano[df_ano["mes"] == mes_sel].copy()

opcoes = []
for _, row in df_mes.iterrows():
    opcoes.append(str(row["nome_arquivo"]) + " - " + str(row["data_geracao"]))

if not opcoes:
    st.warning("Nenhum consolidado encontrado para os filtros selecionados.")
    st.stop()

opcao = st.sidebar.selectbox("Consolidado", opcoes)
idx = opcoes.index(opcao)
consolidado = df_mes.iloc[idx]
consolidado_id = consolidado["consolidado_id"]

nome_arquivo, arquivo_bytes = carregar_arquivo_consolidado(consolidado_id)
if not arquivo_bytes:
    st.error("Arquivo consolidado nao encontrado no banco.")
    st.stop()

try:
    wb = load_workbook(BytesIO(arquivo_bytes), data_only=True)
    df_resultados = extrair_resultados_consolidado(wb)
except Exception as e:
    st.error("Erro ao extrair indicadores do consolidado.")
    st.exception(e)
    st.stop()

if df_resultados.empty:
    st.warning("Nenhum indicador extraido do consolidado.")
    st.stop()

df_farol = montar_base_farol(df_resultados, df_metas, int(ano_sel), int(mes_sel))
df_tabela_farol, status_celulas = montar_tabela_farol(df_farol, df_metas, int(ano_sel), int(mes_sel))
df_status = calcular_status_por_planta(df_farol)

st.subheader("Resumo")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Arquivo", nome_arquivo)
col2.metric("Ano", int(ano_sel))
col3.metric("Mes", int(mes_sel))
col4.metric("Indicadores avaliados", int(df_farol["Status"].isin(["verde", "vermelho"]).sum()))

st.download_button(
    "Baixar arquivo consolidado",
    data=arquivo_bytes,
    file_name=nome_arquivo,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.divider()

tab_farol, tab_status, tab_detalhes, tab_historico, tab_admin = st.tabs([
    "Farol Mensal",
    "Status Indicador MTD",
    "Detalhes",
    "Historico",
    "Administracao",
])

with tab_farol:
    st.subheader("Farol de Indicadores Mensais CN - " + str(int(mes_sel)).zfill(2) + "/" + str(int(ano_sel)))
    st.caption("Regional CN exibe Meta quando cadastrada, mas MTD CN permanece NA e nao entra no calculo de status.")
    st.dataframe(estilizar_tabela_farol(df_tabela_farol, status_celulas), use_container_width=True, hide_index=True)

with tab_status:
    st.subheader("Status Indicador (MTD)")
    st.caption("CN nao e calculado neste grafico. O status considera apenas COB, CUI, EDE, NOB, PVE, SOB e XAM.")
    if df_status.empty:
        st.info("Nao ha indicadores suficientes com meta e resultado para montar o status MTD.")
    else:
        fig = plot_status_mtd(df_status)
        st.pyplot(fig, use_container_width=False)
        st.dataframe(df_status, use_container_width=True, hide_index=True)

with tab_detalhes:
    st.subheader("Base detalhada do farol")
    plantas = sorted(df_farol["Codigo"].dropna().unique())
    grupos = sorted(df_farol["Grupo"].dropna().unique())
    indicadores = sorted(df_farol["Indicador"].dropna().unique())
    c1, c2, c3 = st.columns(3)
    with c1:
        f_plantas = st.multiselect("Plantas", plantas, default=plantas)
    with c2:
        f_grupos = st.multiselect("Grupos", grupos, default=grupos)
    with c3:
        f_ind = st.multiselect("Indicadores", indicadores, default=indicadores)
    df_view = df_farol[
        df_farol["Codigo"].isin(f_plantas)
        & df_farol["Grupo"].isin(f_grupos)
        & df_farol["Indicador"].isin(f_ind)
    ].copy()
    st.dataframe(df_view, use_container_width=True, hide_index=True)
    csv = df_view.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Baixar detalhes em CSV", data=csv, file_name="farol_consolidado_detalhado.csv", mime="text/csv")

with tab_historico:
    st.subheader("Historico de consolidados")
    cols = ["nome_arquivo", "data_processada", "ano", "mes", "data_geracao"]
    cols = [c for c in cols if c in df_consolidados.columns]
    st.dataframe(df_consolidados[cols], use_container_width=True, hide_index=True)

with tab_admin:
    st.subheader("Administracao")
    with st.expander("Excluir consolidado selecionado"):
        st.warning("Essa acao remove o consolidado do historico compartilhado.")
        if st.button("Excluir consolidado selecionado"):
            excluir_consolidado(consolidado_id)
            st.success("Consolidado excluido.")
            st.rerun()
