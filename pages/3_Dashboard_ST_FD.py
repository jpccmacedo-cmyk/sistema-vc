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
    page_icon="📈",
    layout="wide"
)


# ============================================================
# PARSER DO EXCEL ST & FD
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
        return pd.DataFrame(), ["ST: coluna Planta não encontrada"]

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
        return pd.DataFrame(), ["ST: estrutura inválida"]

    ano = date_cols[0]["date"].year
    mes = date_cols[0]["date"].month

    for i in range(hr + 1, len(df)):
        row = df.iloc[i].tolist()

        planta = str(row[pc]).strip()

        if planta in ["", "nan", "None"]:
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
        return pd.DataFrame(), ["FD: coluna Planta não encontrada"]

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
        return pd.DataFrame(), ["FD: estrutura inválida"]

    ano = date_cols[0]["date"].year
    mes = date_cols[0]["date"].month

    for i in range(hr + 1, len(df)):
        row = df.iloc[i].tolist()

        planta = str(row[pc]).strip()

        if planta in ["", "nan", "None"]:
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

        if ("diário" in nome or "diario" in nome) and "st" in nome:
            st_sheet = sheet

        if ("diário" in nome or "diario" in nome) and "fd" in nome and "multiflex" in nome:
            fd_sheet = sheet

    if st_sheet:
        arquivo.seek(0)

        df_st = pd.read_excel(
            arquivo,
            sheet_name=st_sheet,
            header=None,
            engine="openpyxl"
        )

        parsed, err = parse_st(df_st, batch_id, data_upload)

        if not parsed.empty:
            todos.append(parsed)

        erros.extend(err)
    else:
        erros.append("Aba 'Diário - ST' não encontrada")

    if fd_sheet:
        arquivo.seek(0)

        df_fd = pd.read_excel(
            arquivo,
            sheet_name=fd_sheet,
            header=None,
            engine="openpyxl"
        )

        parsed, err = parse_fd(df_fd, batch_id, data_upload)

        if not parsed.empty:
            todos.append(parsed)

        erros.extend(err)
    else:
        erros.append("Aba 'Diário - FD Multiflex' não encontrada")

    if not todos:
        return pd.DataFrame(), erros

    return pd.concat(todos, ignore_index=True), erros


# ============================================================
# CORES E TABELAS
# ============================================================

def cor_st(valor, m300, rf):
    if pd.isna(valor):
        return "background-color: #ffffff"

    if pd.notna(m300) and pd.notna(rf):
        if valor >= m300 and valor >= rf:
            return "background-color: #C6EFCE"
        if valor < m300 and valor < rf:
            return "background-color: #FFC7CE"
        return "background-color: #FFEB9C"

    if pd.notna(m300):
        return "background-color: #C6EFCE" if valor >= m300 else "background-color: #FFC7CE"

    if pd.notna(rf):
        return "background-color: #C6EFCE" if valor >= rf else "background-color: #FFC7CE"

    return "background-color: #FFEB9C"


def cor_fd(valor):
    if pd.isna(valor):
        return "background-color: #ffffff"

    if valor >= 0.95:
        return "background-color: #C6EFCE"

    if valor >= 0.85:
        return "background-color: #FFEB9C"

    return "background-color: #FFC7CE"


def montar_tabela_st(df_mes):
    df_st = df_mes[df_mes["fonte"] == "ST"].copy()

    if df_st.empty:
        return pd.DataFrame()

    for col in ["valor_real", "m300", "rf", "acumulado_mes"]:
        df_st[col] = pd.to_numeric(df_st[col], errors="coerce")

    linhas = []

    for planta, bloco in df_st.groupby("planta"):
        bloco = bloco.sort_values("dia")

        linha = {
            "Planta": planta,
            "M300": bloco["m300"].dropna().iloc[0] if bloco["m300"].notna().any() else None,
            "RF": bloco["rf"].dropna().iloc[0] if bloco["rf"].notna().any() else None,
        }

        for _, row in bloco.iterrows():
            linha[row["data_label"]] = row["valor_real"]

        linha["Acc mês"] = (
            bloco["acumulado_mes"].dropna().iloc[0]
            if bloco["acumulado_mes"].notna().any()
            else None
        )

        linhas.append(linha)

    return pd.DataFrame(linhas)


def estilizar_st(tabela):
    if tabela.empty:
        return tabela

    dias = [
        c for c in tabela.columns
        if c not in ["Planta", "M300", "RF", "Acc mês"]
    ]

    def aplicar(row):
        estilos = []

        for col in tabela.columns:
            if col in ["Planta", "M300", "RF"]:
                estilos.append("background-color: #eef2f7; font-weight: 600")
            elif col in dias:
                estilos.append(cor_st(row[col], row.get("M300"), row.get("RF")))
            elif col == "Acc mês":
                estilos.append(cor_st(row[col], row.get("M300"), row.get("RF")) + "; font-weight: 700")
            else:
                estilos.append("")

        return estilos

    return tabela.style.apply(aplicar, axis=1).format(precision=2)


def montar_tabela_fd(df_mes):
    df_fd = df_mes[df_mes["fonte"] == "FD"].copy()

    if df_fd.empty:
        return pd.DataFrame()

    for col in ["valor_real", "acumulado_mes"]:
        df_fd[col] = pd.to_numeric(df_fd[col], errors="coerce")

    linhas = []

    for planta, bloco in df_fd.groupby("planta"):
        bloco = bloco.sort_values("dia")

        linha = {
            "Planta": planta
        }

        for _, row in bloco.iterrows():
            linha[row["data_label"]] = row["valor_real"]

        linha["Real TT"] = (
            bloco["acumulado_mes"].dropna().iloc[0]
            if bloco["acumulado_mes"].notna().any()
            else None
        )

        linhas.append(linha)

    return pd.DataFrame(linhas)


def estilizar_fd(tabela):
    if tabela.empty:
        return tabela

    def aplicar(row):
        estilos = []

        for col in tabela.columns:
            if col == "Planta":
                estilos.append("background-color: #eef2f7; font-weight: 600")
            else:
                estilos.append(cor_fd(row[col]))

        return estilos

    format_dict = {
        col: (lambda x: "" if pd.isna(x) else f"{x:.2%}")
        for col in tabela.columns
        if col != "Planta"
    }

    return tabela.style.apply(aplicar, axis=1).format(format_dict)


# ============================================================
# APP
# ============================================================

init_stfd_db()

st.title("📈 Dashboard ST & FD")
st.caption("Dashboard com histórico compartilhado em PostgreSQL.")

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
                st.error("Nenhum registro foi extraído do arquivo.")

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

col1.metric("Uploads salvos", df_uploads["batch_id"].nunique())
col2.metric("Ano selecionado", int(ano_sel))
col3.metric("Mês selecionado", int(mes_sel))
col4.metric("Plantas", df_mes["planta"].nunique())

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
        opcoes = [
            f'{row["nome_arquivo"]} — {row["data_upload"]}'
            for _, row in df_uploads.iterrows()
        ]

        opcao = st.selectbox(
            "Selecionar upload para excluir",
            opcoes
        )

        batch_id_excluir = df_uploads.iloc[opcoes.index(opcao)]["batch_id"]

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
