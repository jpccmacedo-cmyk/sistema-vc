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

st.set_page_config(
    page_title="Dashboard ST & FD",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

PLANTAS_ORDEM = ["COB", "CUI", "EDE", "NOB", "PVE", "SOB", "XAM", "CN"]
PLANTAS_NOMES = {
    "COB": "COB",
    "CUI": "CUI",
    "EDE": "EDE",
    "NOB": "NOB",
    "PVE": "PVE",
    "SOB": "SOB",
    "XAM": "XAM",
    "CN": "CN",
}


# ============================================================
# Normalizacao visual/filtros
# ============================================================

def normalizar_texto_simples(valor):
    texto = "" if valor is None else str(valor)
    texto = texto.strip().upper()
    texto = texto.replace("Á", "A").replace("À", "A").replace("Ã", "A").replace("Â", "A")
    texto = texto.replace("É", "E").replace("Ê", "E")
    texto = texto.replace("Í", "I")
    texto = texto.replace("Ó", "O").replace("Ô", "O").replace("Õ", "O")
    texto = texto.replace("Ú", "U")
    texto = texto.replace("Ç", "C")
    texto = texto.replace("-TOTAL", "").replace("-TOTAL ", "")
    texto = texto.replace("- TOTAL", "").replace(" TOTAL", "")
    texto = " ".join(texto.split())
    return texto


def normalizar_planta(valor):
    texto = normalizar_texto_simples(valor)

    aliases = {
        "CORUMBA": "COB",
        "COB": "COB",
        "CUIABA": "CUI",
        "CUI": "CUI",
        "EDEALINA": "EDE",
        "EDE": "EDE",
        "NOBRES": "NOB",
        "NOB": "NOB",
        "PORTO VELHO": "PVE",
        "PVE": "PVE",
        "SOBRADINHO": "SOB",
        "SOB": "SOB",
        "XAMBIOA": "XAM",
        "XAM": "XAM",
        "CENTRO NORTE": "CN",
        "CENTRO-NORTE": "CN",
        "CN": "CN",
    }

    return aliases.get(texto, texto)


def aplicar_filtro_plantas_padrao(df):
    if df.empty or "planta" not in df.columns:
        return df

    df = df.copy()
    df["planta"] = df["planta"].apply(normalizar_planta)
    df = df[df["planta"].isin(PLANTAS_ORDEM)].copy()
    return df


def ordenar_por_planta(df, coluna="planta"):
    if df.empty or coluna not in df.columns:
        return df

    df = df.copy()
    df["_ordem_planta"] = df[coluna].map({p: i for i, p in enumerate(PLANTAS_ORDEM)})
    df = df.sort_values(["_ordem_planta", coluna]).drop(columns=["_ordem_planta"])
    return df


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


# ============================================================
# Parser do Excel ST & FD
# ============================================================

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

        if texto in ["", "-"]:
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

    pc = -1
    mc = -1
    rc = -1
    rlc = -1
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

    pc = -1
    kc = -1
    ac = -1
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


# ============================================================
# Cores e tabelas
# ============================================================

def cor_st(valor, m300, rf):
    if pd.isna(valor):
        return "background-color: #ffffff; color: #ffffff"

    if pd.notna(m300) and pd.notna(rf):
        if valor >= m300 and valor >= rf:
            return "background-color: #C6EFCE; color: #000000"
        if valor < m300 and valor < rf:
            return "background-color: #FFC7CE; color: #000000"
        return "background-color: #FFEB9C; color: #000000"

    if pd.notna(m300):
        return "background-color: #C6EFCE; color: #000000" if valor >= m300 else "background-color: #FFC7CE; color: #000000"

    if pd.notna(rf):
        return "background-color: #C6EFCE; color: #000000" if valor >= rf else "background-color: #FFC7CE; color: #000000"

    return "background-color: #FFEB9C; color: #000000"


def cor_fd(valor):
    if pd.isna(valor):
        return "background-color: #ffffff; color: #ffffff"

    if valor >= 0.95:
        return "background-color: #C6EFCE; color: #000000"

    if valor >= 0.85:
        return "background-color: #FFEB9C; color: #000000"

    return "background-color: #FFC7CE; color: #000000"


def fmt_decimal(x):
    if pd.isna(x):
        return ""
    return f"{float(x):.2f}".replace(".", ",")


def fmt_percentual(x):
    if pd.isna(x):
        return ""
    return f"{float(x):.2%}".replace(".", ",")


def montar_tabela_st(df_mes):
    df_st = df_mes[df_mes["fonte"] == "ST"].copy()
    df_st = aplicar_filtro_plantas_padrao(df_st)

    if df_st.empty:
        return pd.DataFrame()

    for col in ["valor_real", "m300", "rf", "acumulado_mes"]:
        df_st[col] = pd.to_numeric(df_st[col], errors="coerce")

    linhas = []

    for planta in PLANTAS_ORDEM:
        bloco = df_st[df_st["planta"] == planta].copy()

        if bloco.empty:
            continue

        bloco = bloco.sort_values("dia")

        linha = {
            "Planta": planta,
            "M300": bloco["m300"].dropna().iloc[0] if bloco["m300"].notna().any() else None,
            "RF": bloco["rf"].dropna().iloc[0] if bloco["rf"].notna().any() else None,
        }

        for _, row in bloco.iterrows():
            linha[row["data_label"]] = row["valor_real"]

        linha["Acc mes"] = bloco["acumulado_mes"].dropna().iloc[0] if bloco["acumulado_mes"].notna().any() else None
        linhas.append(linha)

    return pd.DataFrame(linhas)


def estilizar_st(tabela):
    if tabela.empty:
        return tabela

    dias = [c for c in tabela.columns if c not in ["Planta", "M300", "RF", "Acc mes"]]

    def aplicar(row):
        estilos = []

        for col in tabela.columns:
            if col in ["Planta", "M300", "RF"]:
                estilos.append("background-color: #EEF2F7; color: #000000; font-weight: 700")
            elif col in dias:
                estilos.append(cor_st(row[col], row.get("M300"), row.get("RF")))
            elif col == "Acc mes":
                estilos.append(cor_st(row[col], row.get("M300"), row.get("RF")) + "; font-weight: 800")
            else:
                estilos.append("")

        return estilos

    format_dict = {col: fmt_decimal for col in tabela.columns if col != "Planta"}

    table_styles = [
        {
            "selector": "th",
            "props": [
                ("font-weight", "800"),
                ("background-color", "#F8FAFC"),
                ("color", "#0F172A"),
                ("border", "1px solid #CBD5E1"),
                ("text-align", "center"),
            ],
        },
        {
            "selector": "td",
            "props": [
                ("border", "1px solid #CBD5E1"),
                ("text-align", "center"),
                ("font-size", "13px"),
            ],
        },
    ]

    return tabela.style.apply(aplicar, axis=1).format(format_dict).set_table_styles(table_styles)


def montar_tabela_fd(df_mes):
    df_fd = df_mes[df_mes["fonte"] == "FD"].copy()
    df_fd = aplicar_filtro_plantas_padrao(df_fd)

    if df_fd.empty:
        return pd.DataFrame()

    for col in ["valor_real", "acumulado_mes"]:
        df_fd[col] = pd.to_numeric(df_fd[col], errors="coerce")

    linhas = []

    for planta in PLANTAS_ORDEM:
        bloco = df_fd[df_fd["planta"] == planta].copy()

        if bloco.empty:
            continue

        bloco = bloco.sort_values("dia")
        linha = {"Planta": planta}

        for _, row in bloco.iterrows():
            linha[row["data_label"]] = row["valor_real"]

        linha["Real TT"] = bloco["acumulado_mes"].dropna().iloc[0] if bloco["acumulado_mes"].notna().any() else None
        linhas.append(linha)

    return pd.DataFrame(linhas)


def estilizar_fd(tabela):
    if tabela.empty:
        return tabela

    def aplicar(row):
        estilos = []

        for col in tabela.columns:
            if col == "Planta":
                estilos.append("background-color: #EEF2F7; color: #000000; font-weight: 700")
            else:
                estilos.append(cor_fd(row[col]))

        return estilos

    format_dict = {col: fmt_percentual for col in tabela.columns if col != "Planta"}

    return tabela.style.apply(aplicar, axis=1).format(format_dict)


# ============================================================
# App
# ============================================================

init_stfd_db()

st.title("Dashboard ST & FD")
st.caption("Dashboard com historico compartilhado em PostgreSQL.")

st.markdown("""
<div style="display:flex;gap:20px;margin:8px 0 16px 0;font-size:13px;">
  <div><span style="background:#C6EFCE;padding:3px 12px;border-radius:4px;"></span> Dentro da meta</div>
  <div><span style="background:#FFEB9C;padding:3px 12px;border-radius:4px;"></span> Parcial</div>
  <div><span style="background:#FFC7CE;padding:3px 12px;border-radius:4px;"></span> Fora da meta</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("Acoes")

with st.sidebar.expander("Enviar novo Excel", expanded=True):
    arquivo = st.file_uploader(
        "Excel com abas Diario - ST e Diario - FD Multiflex",
        type=["xlsx", "xlsm"]
    )

    usuario = st.text_input("Usuario / responsavel", value="")
    observacao = st.text_area("Observacao", value="")

    if st.button("Salvar upload no historico", disabled=arquivo is None):
        try:
            batch_id, data_upload = criar_batch_upload(
                arquivo.name,
                usuario or None,
                observacao or None
            )

            df_records, erros = parse_st_fd_excel(
                arquivo.getvalue(),
                batch_id,
                data_upload
            )

            if df_records.empty:
                excluir_batch(batch_id)
                st.error("Nenhum registro foi extraido do arquivo.")

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
    st.stop()

st.sidebar.header("Filtros")

anos = sorted(df["ano"].dropna().unique())

ano_sel = st.sidebar.selectbox(
    "Ano",
    anos,
    index=len(anos) - 1
)

df_ano = df[df["ano"] == ano_sel].copy()

meses = sorted(df_ano["mes"].dropna().unique())

mes_sel = st.sidebar.selectbox(
    "Mes",
    meses,
    index=len(meses) - 1
)

df_mes = df_ano[df_ano["mes"] == mes_sel].copy()
df_mes = aplicar_filtro_plantas_padrao(df_mes)

plantas = [p for p in PLANTAS_ORDEM if p in set(df_mes["planta"].dropna().unique())]

plantas_sel = st.sidebar.multiselect(
    "Plantas",
    plantas,
    default=plantas
)

df_mes = df_mes[df_mes["planta"].isin(plantas_sel)].copy()
df_mes = ordenar_por_planta(df_mes, "planta")

data_titulo = data_titulo_heatmap(df_mes, ano_sel, mes_sel)

st.subheader("Resumo")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Uploads salvos", df_uploads["batch_id"].nunique())
col2.metric("Ano selecionado", int(ano_sel))
col3.metric("Mes selecionado", int(mes_sel))
col4.metric("Plantas", df_mes["planta"].nunique())

st.divider()

tab_st, tab_fd, tab_uploads, tab_base = st.tabs([
    "ST Heatmap",
    "FD Multiflex",
    "Historico de uploads",
    "Base filtrada"
])

with tab_st:
    st.subheader("ST Heatmap - " + data_titulo)

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
    st.subheader("FD Multiflex - " + data_titulo)

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
    st.subheader("Historico de uploads")
    st.dataframe(df_uploads, use_container_width=True)

    if not df_uploads.empty:
        opcoes = [
            str(row["nome_arquivo"]) + " - " + str(row["data_upload"])
            for _, row in df_uploads.iterrows()
        ]

        opcao = st.selectbox(
            "Selecionar upload para excluir",
            opcoes
        )

        batch_id_excluir = df_uploads.iloc[opcoes.index(opcao)]["batch_id"]

        if st.button("Excluir upload selecionado"):
            excluir_batch(batch_id_excluir)
            st.success("Upload excluido com sucesso.")
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
