import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO

from database.stfd_db import (
    init_stfd_db,
    criar_batch_upload,
    salvar_records_stfd,
    listar_uploads,
    carregar_records,
    excluir_batch,
)

try:
    from utils.ui_vc import (
        configurar_pagina,
        aplicar_css_global,
        render_header,
        render_sidebar_logo,
        render_footer,
    )
except Exception:
    def configurar_pagina(titulo, icone=":bar_chart:", layout="wide"):
        st.set_page_config(page_title=titulo, page_icon=icone, layout=layout)

    def aplicar_css_global(max_width="100%", esconder_sidebar=False):
        st.markdown(
            f"""
            <style>
                .block-container {{
                    max-width:{max_width}!important;
                    padding-left:.75rem!important;
                    padding-right:.75rem!important;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    def render_header(titulo, subtitulo="", mostrar_logo=True):
        st.title(titulo)
        if subtitulo:
            st.caption(subtitulo)

    def render_sidebar_logo(texto="Regional Centro-Norte"):
        st.sidebar.caption(texto)
        st.sidebar.markdown("---")

    def render_footer():
        st.caption("Votorantim Cimentos | Regional Centro-Norte")


configurar_pagina(
    titulo="Dashboard ST & FD | Sistema CN",
    icone=":chart_with_upwards_trend:",
    layout="wide",
)
aplicar_css_global(max_width="100%")
render_sidebar_logo()

PLANTAS_ORDEM = ["COB", "CUI", "EDE", "NOB", "PVE", "SOB", "XAM", "CN"]

st.markdown(
    """
    <style>
        .block-container {
            max-width: 100% !important;
            padding-left: 0.45rem !important;
            padding-right: 0.45rem !important;
            padding-top: 1.1rem !important;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 0.65rem;
        }
        .heatmap-wrap {
            width: 100%;
            overflow-x: auto;
            overflow-y: hidden;
            background: #ffffff;
            padding-bottom: 6px;
        }
        table.heatmap-table {
            border-collapse: collapse;
            font-family: Calibri, Arial, Helvetica, sans-serif !important;
            font-size: 12px !important;
            background: #ffffff;
            color: #000000;
            table-layout: auto;
            width: max-content;
            min-width: 100%;
            font-weight: 400 !important;
        }
        .heatmap-table th,
        .heatmap-table td {
            border: 1px solid #D9EAF7;
            padding: 4px 7px;
            text-align: center;
            white-space: nowrap;
            height: 23px;
            line-height: 1.05;
            font-weight: 400 !important;
            font-style: normal !important;
            vertical-align: middle;
            font-family: Calibri, Arial, Helvetica, sans-serif !important;
        }
        .heatmap-table th {
            background: #F7FBFF;
            color: #000000;
            font-weight: 400 !important;
        }
        .heatmap-table td.planta {
            background: #FFFFFF;
            color: #000000;
            font-weight: 400 !important;
            text-align: left;
            min-width: 42px;
        }
        .heatmap-table td.base {
            background: #FFFFFF;
            color: #000000;
            font-weight: 400 !important;
            min-width: 43px;
        }
        .heatmap-table td.valor {
            color: #000000;
            font-weight: 400 !important;
            min-width: 45px;
        }
        .legend-row {
            display: flex;
            gap: 18px;
            align-items: center;
            margin: 8px 0 16px 0;
            font-size: 12px;
            font-family: Calibri, Arial, Helvetica, sans-serif;
        }
        .legend-box {
            display: inline-block;
            width: 18px;
            height: 18px;
            border-radius: 3px;
            margin-right: 4px;
            vertical-align: middle;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalizar_texto_simples(valor):
    texto = "" if valor is None else str(valor)
    texto = texto.strip().upper()
    texto = texto.replace("Á", "A").replace("À", "A").replace("Ã", "A").replace("Â", "A")
    texto = texto.replace("É", "E").replace("Ê", "E")
    texto = texto.replace("Í", "I")
    texto = texto.replace("Ó", "O").replace("Ô", "O").replace("Õ", "O")
    texto = texto.replace("Ú", "U").replace("Ç", "C")
    texto = texto.replace("-TOTAL", "").replace("-TOTAL ", "")
    texto = texto.replace("- TOTAL", "").replace(" TOTAL", "")
    texto = " ".join(texto.split())
    return texto


def normalizar_planta(valor):
    texto = normalizar_texto_simples(valor)
    aliases = {
        "CORUMBA": "COB", "COB": "COB",
        "CUIABA": "CUI", "CUI": "CUI",
        "EDEALINA": "EDE", "EDE": "EDE",
        "NOBRES": "NOB", "NOB": "NOB",
        "PORTO VELHO": "PVE", "PVE": "PVE",
        "SOBRADINHO": "SOB", "SOB": "SOB",
        "XAMBIOA": "XAM", "XAM": "XAM",
        "CENTRO NORTE": "CN", "CENTRO-NORTE": "CN", "CN": "CN",
    }
    return aliases.get(texto, texto)


def aplicar_filtro_plantas_padrao(df):
    if df.empty or "planta" not in df.columns:
        return df
    df = df.copy()
    df["planta"] = df["planta"].apply(normalizar_planta)
    return df[df["planta"].isin(PLANTAS_ORDEM)].copy()


def ordenar_por_planta(df, coluna="planta"):
    if df.empty or coluna not in df.columns:
        return df
    df = df.copy()
    df["_ordem_planta"] = df[coluna].map({p: i for i, p in enumerate(PLANTAS_ORDEM)})
    return df.sort_values(["_ordem_planta", coluna]).drop(columns=["_ordem_planta"])


def ultimo_dia_mes(ano, mes):
    ano = int(ano)
    mes = int(mes)
    if mes == 12:
        prox = datetime(ano + 1, 1, 1)
    else:
        prox = datetime(ano, mes + 1, 1)
    atual = datetime(ano, mes, 1)
    return (prox - atual).days


def data_titulo_heatmap(df_mes, ano, mes):
    try:
        df_aux = df_mes.copy()
        df_aux["valor_real_num"] = pd.to_numeric(df_aux["valor_real"], errors="coerce")
        df_aux["dia_num"] = pd.to_numeric(df_aux["dia"], errors="coerce")
        df_validos = df_aux[df_aux["valor_real_num"].notna() & df_aux["dia_num"].notna()]
        if not df_validos.empty:
            dia = int(df_validos["dia_num"].max())
            return f"{dia:02d}/{int(mes):02d}/{int(ano)}"
    except Exception:
        pass
    return f"01/{int(mes):02d}/{int(ano)}"


def pv(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        texto = v.replace(",", ".").replace("%", "").strip()
        if texto in ["", "-", "None", "none", "NONE", "nan", "NaN", "NAN", "<NA>"]:
            return None
        try:
            return float(texto)
        except Exception:
            return None
    return None


def excel_serial_to_date(serial):
    return datetime(1899, 12, 30) + pd.to_timedelta(serial, unit="D")


def parse_date(v):
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    if isinstance(v, (int, float)) and 40000 < v < 60000:
        return excel_serial_to_date(v)
    if isinstance(v, str):
        texto = v.strip()
        if not texto:
            return None
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]:
            try:
                return datetime.strptime(texto[:10], fmt)
            except Exception:
                pass
        try:
            data = pd.to_datetime(texto, dayfirst=True, errors="coerce")
            if pd.notna(data):
                return data.to_pydatetime()
        except Exception:
            pass
    return None


def find_header_row(df, keyword="Planta"):
    for i in range(min(10, len(df))):
        for cell in df.iloc[i].tolist():
            if str(cell).strip().lower().startswith(keyword.lower()):
                return i
    return -1


def parse_st(df, batch_id, data_upload):
    registros = []
    erros = []
    hr = find_header_row(df, "Planta")
    if hr < 0:
        return pd.DataFrame(), ["ST: coluna Planta nao encontrada"]

    header = df.iloc[hr].tolist()
    pc = mc = rc = rlc = -1
    date_cols = []

    for j, value in enumerate(header):
        texto = str(value).strip()
        texto_lower = texto.lower()
        if texto_lower.startswith("planta"):
            pc = j
        elif texto == "M300":
            mc = j
        elif texto == "RF":
            rc = j
        elif texto_lower == "real":
            rlc = j
        else:
            data = parse_date(value)
            if data:
                date_cols.append({"col": j, "date": data})

    if pc < 0 or not date_cols:
        return pd.DataFrame(), ["ST: estrutura invalida"]

    ano = date_cols[0]["date"].year
    mes = date_cols[0]["date"].month

    for i in range(hr + 1, len(df)):
        row = df.iloc[i].tolist()
        planta = normalizar_planta(row[pc])
        if planta not in PLANTAS_ORDEM:
            continue

        m300 = pv(row[mc]) if mc >= 0 else None
        rf = pv(row[rc]) if rc >= 0 else None
        acumulado = pv(row[rlc]) if rlc >= 0 else None

        for dc in date_cols:
            data = dc["date"]
            registros.append({
                "batch_id": batch_id,
                "fonte": "ST",
                "ano": ano,
                "mes": mes,
                "planta": planta,
                "kpi": "ST",
                "dia": data.day,
                "data_label": data.strftime("%d/%m"),
                "valor_real": pv(row[dc["col"]]),
                "m300": m300,
                "rf": rf,
                "acumulado_mes": acumulado,
                "data_upload": data_upload,
            })
    return pd.DataFrame(registros), erros


def parse_fd(df, batch_id, data_upload):
    registros = []
    erros = []
    hr = find_header_row(df, "Planta")
    if hr < 0:
        return pd.DataFrame(), ["FD: coluna Planta nao encontrada"]

    header = df.iloc[hr].tolist()
    pc = kc = ac = -1
    date_cols = []

    for j, value in enumerate(header):
        texto = str(value).strip()
        texto_lower = texto.lower()
        if texto_lower.startswith("planta"):
            pc = j
        elif texto_lower == "kpi":
            kc = j
        elif "real" in texto_lower and "tt" in texto_lower:
            ac = j
        else:
            data = parse_date(value)
            if data:
                date_cols.append({"col": j, "date": data})

    if pc < 0 or not date_cols:
        return pd.DataFrame(), ["FD: estrutura invalida"]

    ano = date_cols[0]["date"].year
    mes = date_cols[0]["date"].month

    for i in range(hr + 1, len(df)):
        row = df.iloc[i].tolist()
        planta = normalizar_planta(row[pc])
        if planta not in PLANTAS_ORDEM:
            continue

        kpi = str(row[kc]).strip() if kc >= 0 else "FD Multiflex"
        if kpi in ["", "nan", "None"]:
            kpi = "FD Multiflex"

        acumulado = pv(row[ac]) if ac >= 0 else None
        if acumulado is not None and acumulado > 1:
            acumulado = acumulado / 100

        for dc in date_cols:
            data = dc["date"]
            valor = pv(row[dc["col"]])
            if valor is not None and valor > 1:
                valor = valor / 100
            registros.append({
                "batch_id": batch_id,
                "fonte": "FD",
                "ano": ano,
                "mes": mes,
                "planta": planta,
                "kpi": kpi,
                "dia": data.day,
                "data_label": data.strftime("%d/%m"),
                "valor_real": valor,
                "m300": None,
                "rf": None,
                "acumulado_mes": acumulado,
                "data_upload": data_upload,
            })
    return pd.DataFrame(registros), erros


def parse_st_fd_excel(file_bytes, batch_id, data_upload):
    arquivo = BytesIO(file_bytes)
    xls = pd.ExcelFile(arquivo, engine="openpyxl")
    todos = []
    erros = []
    st_sheet = None
    fd_sheet = None
    for sheet in xls.sheet_names:
        nome = sheet.lower()
        if ("diario" in nome or "diário" in nome) and "st" in nome:
            st_sheet = sheet
        if ("diario" in nome or "diário" in nome) and "fd" in nome and "multiflex" in nome:
            fd_sheet = sheet

    if st_sheet:
        arquivo.seek(0)
        df_st = pd.read_excel(arquivo, sheet_name=st_sheet, header=None, engine="openpyxl")
        parsed, err = parse_st(df_st, batch_id, data_upload)
        if not parsed.empty:
            todos.append(parsed)
        erros.extend(err)
    else:
        erros.append("Aba Diario - ST nao encontrada")

    if fd_sheet:
        arquivo.seek(0)
        df_fd = pd.read_excel(arquivo, sheet_name=fd_sheet, header=None, engine="openpyxl")
        parsed, err = parse_fd(df_fd, batch_id, data_upload)
        if not parsed.empty:
            todos.append(parsed)
        erros.extend(err)
    else:
        erros.append("Aba Diario - FD Multiflex nao encontrada")

    if not todos:
        return pd.DataFrame(), erros
    return pd.concat(todos, ignore_index=True), erros


def valor_vazio(valor):
    if valor is None:
        return True
    try:
        if pd.isna(valor):
            return True
    except Exception:
        pass
    if isinstance(valor, str) and valor.strip() in ["", "None", "none", "NONE", "nan", "NaN", "NAN", "<NA>"]:
        return True
    return False


def ultimo_valor_valido(serie):
    for valor in reversed(list(serie)):
        if not valor_vazio(valor):
            return valor
    return None


def ordenar_registros_recentes(df):
    cols = []
    if "data_upload" in df.columns:
        cols.append("data_upload")
    if "batch_id" in df.columns:
        cols.append("batch_id")
    if "dia" in df.columns:
        cols.append("dia")
    if not cols:
        return df
    return df.sort_values(cols, kind="stable")


def fmt_decimal(valor):
    if valor_vazio(valor):
        return ""
    return f"{float(valor):.2f}".replace(".", ",")


def fmt_percentual(valor):
    if valor_vazio(valor):
        return ""
    return f"{float(valor):.2%}".replace(".", ",")


def cor_st_hex(valor, m300, rf):
    if valor_vazio(valor):
        return "#FFFFFF"
    valor = float(valor)
    if not valor_vazio(m300) and not valor_vazio(rf):
        m300 = float(m300)
        rf = float(rf)
        if valor >= m300 and valor >= rf:
            return "#C6EFCE"
        if valor < m300 and valor < rf:
            return "#FFC7CE"
        return "#FFE699"
    if not valor_vazio(m300):
        return "#C6EFCE" if valor >= float(m300) else "#FFC7CE"
    if not valor_vazio(rf):
        return "#C6EFCE" if valor >= float(rf) else "#FFC7CE"
    return "#FFE699"


def cor_fd_hex(valor):
    if valor_vazio(valor):
        return "#FFFFFF"
    valor = float(valor)
    if valor >= 0.95:
        return "#C6EFCE"
    if valor >= 0.85:
        return "#FFE699"
    return "#FFC7CE"


def montar_tabela_st(df_mes, ano, mes):
    df_st = df_mes[df_mes["fonte"] == "ST"].copy()
    df_st = aplicar_filtro_plantas_padrao(df_st)
    if df_st.empty:
        return pd.DataFrame()

    for col in ["valor_real", "m300", "rf", "acumulado_mes", "dia"]:
        df_st[col] = pd.to_numeric(df_st[col], errors="coerce")
    df_st = ordenar_registros_recentes(df_st)

    linhas = []
    max_dia = ultimo_dia_mes(ano, mes)
    dias_labels = [f"{d:02d}/{int(mes):02d}" for d in range(1, max_dia + 1)]

    for planta in PLANTAS_ORDEM:
        bloco = df_st[df_st["planta"] == planta].copy()
        if bloco.empty:
            continue

        valores_por_dia = {}
        for dia, grupo in bloco.groupby("dia", sort=True):
            if pd.isna(dia):
                continue
            valores_por_dia[int(dia)] = ultimo_valor_valido(grupo["valor_real"])

        linha = {
            "Planta": planta,
            "M300": ultimo_valor_valido(bloco["m300"]),
            "RF": ultimo_valor_valido(bloco["rf"]),
        }
        for d, label in enumerate(dias_labels, start=1):
            linha[label] = valores_por_dia.get(d, None)
        linha["Acc mês"] = ultimo_valor_valido(bloco["acumulado_mes"])
        linhas.append(linha)
    return pd.DataFrame(linhas)


def montar_tabela_fd(df_mes, ano, mes):
    df_fd = df_mes[df_mes["fonte"] == "FD"].copy()
    df_fd = aplicar_filtro_plantas_padrao(df_fd)
    if df_fd.empty:
        return pd.DataFrame()

    for col in ["valor_real", "acumulado_mes", "dia"]:
        df_fd[col] = pd.to_numeric(df_fd[col], errors="coerce")
    df_fd = ordenar_registros_recentes(df_fd)

    linhas = []
    max_dia = ultimo_dia_mes(ano, mes)
    dias_labels = [f"{d:02d}/{int(mes):02d}" for d in range(1, max_dia + 1)]

    for planta in PLANTAS_ORDEM:
        bloco = df_fd[df_fd["planta"] == planta].copy()
        if bloco.empty:
            continue

        valores_por_dia = {}
        for dia, grupo in bloco.groupby("dia", sort=True):
            if pd.isna(dia):
                continue
            valores_por_dia[int(dia)] = ultimo_valor_valido(grupo["valor_real"])

        linha = {"Planta": planta}
        for d, label in enumerate(dias_labels, start=1):
            linha[label] = valores_por_dia.get(d, None)
        linha["Real TT"] = ultimo_valor_valido(bloco["acumulado_mes"])
        linhas.append(linha)
    return pd.DataFrame(linhas)


def tabela_heatmap_html(tabela, tipo="ST"):
    if tabela.empty:
        return ""
    html = "<div class='heatmap-wrap'><table class='heatmap-table'><thead><tr>"
    for col in tabela.columns:
        html += "<th style='font-weight:400 !important;'>" + str(col) + "</th>"
    html += "</tr></thead><tbody>"

    for _, row in tabela.iterrows():
        html += "<tr>"
        for col in tabela.columns:
            if col == "Planta":
                html += "<td class='planta' style='font-weight:400 !important;'>" + str(row[col]) + "</td>"
            elif tipo == "ST" and col in ["M300", "RF"]:
                html += "<td class='base' style='font-weight:400 !important;'>" + fmt_decimal(row[col]) + "</td>"
            elif tipo == "ST":
                bg = cor_st_hex(row[col], row.get("M300"), row.get("RF"))
                html += "<td class='valor' style='background:" + bg + ";font-weight:400 !important;'>" + fmt_decimal(row[col]) + "</td>"
            else:
                bg = cor_fd_hex(row[col])
                html += "<td class='valor' style='background:" + bg + ";font-weight:400 !important;'>" + fmt_percentual(row[col]) + "</td>"
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


init_stfd_db()

render_header(
    titulo="Dashboard ST & FD",
    subtitulo="ST Heatmap e FD Multiflex | Regional Centro-Norte",
)

st.markdown(
    """
    <div class="legend-row">
      <div><span class="legend-box" style="background:#C6EFCE;"></span>Dentro da meta</div>
      <div><span class="legend-box" style="background:#FFE699;"></span>Parcial</div>
      <div><span class="legend-box" style="background:#FFC7CE;"></span>Fora da meta</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Ações")
with st.sidebar.expander("Enviar novo Excel", expanded=True):
    arquivo = st.file_uploader("Excel com abas Diário - ST e Diário - FD Multiflex", type=["xlsx", "xlsm"])
    usuario = st.text_input("Usuário / responsável", value="")
    observacao = st.text_area("Observação", value="")
    if st.button("Salvar upload no histórico", disabled=arquivo is None):
        try:
            batch_id, data_upload = criar_batch_upload(arquivo.name, usuario or None, observacao or None)
            df_records, erros = parse_st_fd_excel(arquivo.getvalue(), batch_id, data_upload)
            if df_records.empty:
                excluir_batch(batch_id)
                st.error("Nenhum registro foi extraído do arquivo.")
                for erro in erros:
                    st.write("- " + str(erro))
                st.stop()
            qtd = salvar_records_stfd(df_records)
            st.success(f"Upload salvo com sucesso. {qtd} registro(s) gravado(s).")
            if erros:
                st.warning("Avisos encontrados:")
                for erro in erros:
                    st.write("- " + str(erro))
            st.rerun()
        except Exception as e:
            st.error("Erro ao salvar upload: " + str(e))


df_uploads = listar_uploads()
df = carregar_records()
df = aplicar_filtro_plantas_padrao(df)

if df.empty:
    st.info("Nenhum dado ST/FD salvo ainda. Envie um Excel no menu lateral.")
    render_footer()
    st.stop()

st.sidebar.header("Filtros")
anos = sorted(df["ano"].dropna().unique())
ano_sel = st.sidebar.selectbox("Ano", anos, index=len(anos) - 1)
df_ano = df[df["ano"] == ano_sel].copy()
meses = sorted(df_ano["mes"].dropna().unique())
mes_sel = st.sidebar.selectbox("Mês", meses, index=len(meses) - 1)
df_mes = df_ano[df_ano["mes"] == mes_sel].copy()
df_mes = aplicar_filtro_plantas_padrao(df_mes)
plantas = [p for p in PLANTAS_ORDEM if p in set(df_mes["planta"].dropna().unique())]
plantas_sel = st.sidebar.multiselect("Plantas", plantas, default=plantas)
df_mes = df_mes[df_mes["planta"].isin(plantas_sel)].copy()
df_mes = ordenar_por_planta(df_mes, "planta")
data_titulo = data_titulo_heatmap(df_mes, ano_sel, mes_sel)

st.subheader("Resumo")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Uploads salvos", df_uploads["batch_id"].nunique())
col2.metric("Ano selecionado", int(ano_sel))
col3.metric("Mês selecionado", int(mes_sel))
col4.metric("Plantas", df_mes["planta"].nunique())

st.divider()

tab_st, tab_fd, tab_uploads, tab_base = st.tabs(["ST", "FD Multiflex", "Histórico de uploads", "Base filtrada"])

with tab_st:
    st.subheader("ST - " + data_titulo)
    tabela_st = montar_tabela_st(df_mes, ano_sel, mes_sel)
    if tabela_st.empty:
        st.info("Nenhum dado ST para os filtros selecionados.")
    else:
        st.markdown(tabela_heatmap_html(tabela_st, tipo="ST"), unsafe_allow_html=True)

with tab_fd:
    st.subheader("FD Multiflex - " + data_titulo)
    tabela_fd = montar_tabela_fd(df_mes, ano_sel, mes_sel)
    if tabela_fd.empty:
        st.info("Nenhum dado FD para os filtros selecionados.")
    else:
        st.markdown(tabela_heatmap_html(tabela_fd, tipo="FD"), unsafe_allow_html=True)

with tab_uploads:
    st.subheader("Histórico de uploads")
    st.dataframe(df_uploads, use_container_width=True)
    if not df_uploads.empty:
        opcoes = [str(row["nome_arquivo"]) + " - " + str(row["data_upload"]) for _, row in df_uploads.iterrows()]
        opcao = st.selectbox("Selecionar upload para excluir", opcoes)
        batch_id_excluir = df_uploads.iloc[opcoes.index(opcao)]["batch_id"]
        if st.button("Excluir upload selecionado"):
            excluir_batch(batch_id_excluir)
            st.success("Upload excluído com sucesso.")
            st.rerun()

with tab_base:
    st.subheader("Base filtrada")
    st.dataframe(df_mes, use_container_width=True)
    csv = df_mes.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Baixar CSV filtrado", data=csv, file_name="historico_st_fd_filtrado.csv", mime="text/csv")

render_footer()
