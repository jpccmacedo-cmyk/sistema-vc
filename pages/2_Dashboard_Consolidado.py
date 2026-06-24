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

from utils.ui_vc import (
    configurar_pagina,
    aplicar_css_global,
    render_header,
    render_sidebar_logo,
    render_footer,
)

configurar_pagina(
    titulo="Dashboard Consolidado | Sistema CN",
    icone=":bar_chart:",
    layout="wide",
)
aplicar_css_global(max_width="100%")
render_sidebar_logo()

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
    return "01/" + str(int(mes)).zfill(2) + "/" + str(int(ano))


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


def css_status(status):
    if status == "verde":
        return "background:#00B050;color:#FFFFFF;font-weight:800;"
    if status == "vermelho":
        return "background:#FF0000;color:#FFFFFF;font-weight:800;"
    if status == "informativo":
        return "background:#D9D9D9;color:#000000;font-weight:800;"
    if status == "sem_meta":
        return "background:#EFEFEF;color:#666666;font-weight:700;"
    return "background:#C9C9C9;color:#000000;font-weight:800;"


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
        lista_indicadores = INDICADORES_ORDEM.get(grupo, [])
        indicador_idx = lista_indicadores.index(indicador) if indicador in lista_indicadores else 99
        return grupo_idx, indicador_idx, grupo, indicador

    return sorted(pares, key=chave_ordem)


def obter_valores_celula(df_farol, df_metas, ano, mes, codigo, grupo, indicador):
    meta_row = buscar_meta(df_metas, ano, mes, codigo, grupo, indicador)
    if meta_row is None:
        meta = None
        tipo = None
    else:
        meta = to_float(meta_row.get("meta"))
        tipo = meta_row.get("tipo")

    if codigo == "CN":
        return meta, None, tipo, "sem_resultado"

    resultado_row = df_farol[
        (df_farol["Codigo"] == codigo)
        & (df_farol["Grupo"] == grupo)
        & (df_farol["Indicador"] == indicador)
    ]

    if resultado_row.empty:
        return meta, None, tipo, "sem_resultado"

    resultado = resultado_row.iloc[0]["Resultado"]
    status = resultado_row.iloc[0]["Status"]
    tipo_resultado = resultado_row.iloc[0].get("Tipo", tipo)
    if tipo_resultado is not None:
        tipo = tipo_resultado

    return meta, resultado, tipo, status


def gerar_farol_html(df_farol, df_metas, ano, mes, data_farol):
    pares = pares_grupo_indicador(df_farol, df_metas, ano, mes)
    total_cols = 1 + len(PLANTAS_ORDEM) * 2

    css = """
    <style>
      .farol-wrapper {
        background: #ffffff;
        padding: 12px 14px 18px 14px;
        border-radius: 0px;
        overflow-x: auto;
        width: 100%;
      }
      .farol-title {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 24px;
        line-height: 1.15;
        font-weight: 900;
        color: #000000;
        text-align: center;
        margin: 0 0 10px 0;
      }
      table.farol-table {
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 13px;
        color: #000000;
        margin: 0 auto;
        background: #ffffff;
      }
      .farol-table th, .farol-table td {
        border: 1px solid #000000;
        padding: 3px 6px;
        text-align: center;
        vertical-align: middle;
        min-width: 74px;
        height: 22px;
        line-height: 1.1;
      }
      .farol-table th.planta {
        font-weight: 900;
        font-size: 14px;
        background: #ffffff;
        color: #000000;
      }
      .farol-table th.subhead {
        font-weight: 500;
        background: #ffffff;
        color: #000000;
      }
      .farol-table td.indicador {
        min-width: 118px;
        text-align: left;
        font-weight: 700;
        background: #ffffff;
      }
      .farol-table tr.grupo-row td {
        background: #BFBFBF;
        font-weight: 900;
        text-align: left;
        height: 22px;
      }
      .farol-table td.meta {
        background: #ffffff;
        color: #000000;
        font-weight: 500;
      }
      .farol-table td.na-cell {
        background: #C9C9C9;
        color: #000000;
        font-weight: 900;
      }
      .farol-table td.blank-gray {
        background: #C9C9C9;
        color: #000000;
        font-weight: 700;
      }
      .copy-note {
        font-family: Arial, Helvetica, sans-serif;
        color: #6B7280;
        font-size: 12px;
        text-align: right;
        margin-top: 6px;
      }
    </style>
    """

    html = css
    html += "<div class='farol-wrapper' id='farol-copiavel'>"
    html += "<div class='farol-title'>Farol de Indicadores Mensais CN - " + data_farol + "</div>"
    html += "<table class='farol-table'>"

    html += "<thead>"
    html += "<tr>"
    html += "<th style='border-top:1px solid #ffffff;border-left:1px solid #ffffff;background:#ffffff;'></th>"
    for _, nome_planta in PLANTAS_ORDEM:
        html += "<th class='planta' colspan='2'>" + nome_planta + "</th>"
    html += "</tr>"

    html += "<tr>"
    html += "<th style='border-left:1px solid #ffffff;background:#ffffff;'></th>"
    for _, _nome_planta in PLANTAS_ORDEM:
        html += "<th class='subhead'>Meta</th><th class='subhead'>MTD</th>"
    html += "</tr>"
    html += "</thead>"

    html += "<tbody>"
    grupo_atual = None
    for grupo, indicador in pares:
        if grupo != grupo_atual:
            grupo_atual = grupo
            if grupo == "Estoques":
                html += "<tr class='grupo-row'><td>Estoques</td>"
                for _, _nome_planta in PLANTAS_ORDEM:
                    html += "<td>Cap.</td><td>Real</td>"
                html += "</tr>"
            else:
                html += "<tr class='grupo-row'><td>" + str(grupo) + "</td>"
                for _ in range(total_cols - 1):
                    html += "<td></td>"
                html += "</tr>"

        html += "<tr>"
        html += "<td class='indicador'>" + str(indicador) + "</td>"

        for codigo, _nome_planta in PLANTAS_ORDEM:
            meta, resultado, tipo, status = obter_valores_celula(df_farol, df_metas, ano, mes, codigo, grupo, indicador)
            meta_txt = formatar_numero(meta, tipo)
            resultado_txt = formatar_numero(resultado, tipo)

            if meta_txt == "NA":
                html += "<td class='blank-gray'>NA</td>"
            else:
                html += "<td class='meta'>" + meta_txt + "</td>"

            if resultado_txt == "NA":
                html += "<td class='na-cell'>NA</td>"
            else:
                html += "<td style='" + css_status(status) + "'>" + resultado_txt + "</td>"

        html += "</tr>"

    html += "</tbody></table>"
    html += "<div class='copy-note'>Dica: use o print da area do navegador ou copie o bloco visual do farol.</div>"
    html += "</div>"
    return html


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
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    y = range(len(df_status))
    acima = df_status["Acima Meta MTD"]
    abaixo = df_status["Abaixo Meta MTD"]
    labels = df_status["Codigo"]

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.barh(y, acima, color="#109618", label="Acima Meta MTD", height=0.78)
    ax.barh(y, abaixo, left=acima, color="#D64550", label="Abaixo Meta MTD", height=0.78)

    for i, (a, b) in enumerate(zip(acima, abaixo)):
        if a > 5:
            ax.text(a / 2, i, f"{a:.2f}%".replace(".", ","), va="center", ha="center", color="white", fontsize=11, fontweight="600")
        if b > 5:
            ax.text(a + b / 2, i, f"{b:.2f}%".replace(".", ","), va="center", ha="center", color="white", fontsize=11, fontweight="600")

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=12, fontweight="700")
    ax.set_xlim(0, 100)
    ax.set_xlabel("")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=2, frameon=False, fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(axis="y", length=0)
    fig.subplots_adjust(top=0.82, left=0.08, right=0.98, bottom=0.05)
    return fig


init_consolidados_db()
init_metas_db()

render_header(
    titulo="Dashboard Consolidado",
    subtitulo="Farol mensal por planta, status MTD e histórico compartilhado | Regional Centro-Norte",
)

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

data_farol = formatar_data_farol(consolidado, ano_sel, mes_sel)

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
df_status = calcular_status_por_planta(df_farol)
html_farol = gerar_farol_html(df_farol, df_metas, int(ano_sel), int(mes_sel), data_farol)

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
    st.markdown(html_farol, unsafe_allow_html=True)
    st.download_button(
        "Baixar farol em HTML",
        data=html_farol.encode("utf-8"),
        file_name="farol_mensal_cn.html",
        mime="text/html"
    )

with tab_status:
    st.markdown(
        "<h2 style='text-align:center; color:#1A2A8F; font-weight:900; margin-bottom:18px;'>Status Indicador (MTD)</h2>",
        unsafe_allow_html=True
    )
    st.caption("CN nao e calculado neste grafico. O status considera apenas COB, CUI, EDE, NOB, PVE, SOB e XAM.")
    if df_status.empty:
        st.info("Nao ha indicadores suficientes com meta e resultado para montar o status MTD.")
    else:
        fig = plot_status_mtd(df_status)
        st.pyplot(fig, use_container_width=True)
        df_status_exibir = df_status.copy()
        df_status_exibir["Acima Meta MTD"] = df_status_exibir["Acima Meta MTD"].map(lambda x: f"{x:.2f}%".replace(".", ","))
        df_status_exibir["Abaixo Meta MTD"] = df_status_exibir["Abaixo Meta MTD"].map(lambda x: f"{x:.2f}%".replace(".", ","))
        st.dataframe(df_status_exibir, use_container_width=True, hide_index=True)

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

render_footer()
