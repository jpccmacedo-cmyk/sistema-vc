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


# ============================================================
# PARSER ST & FD DIRETO NA PÁGINA
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
        c = v.replace(",", ".").replace("%", "").strip()

        if c in ["", "-"]:
            return None

        try:
            return float(c)
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
            d = pd.to_datetime(texto, dayfirst=True, errors="coerce")

            if pd.notna(d):
                return d.to_pydatetime()
        except Exception:
            pass

    return None


def find_header_row(df, keyword):
    max_rows = min(10, len(df))

    for i in range(max_rows):
        row = df.iloc[i].tolist()

        for cell in row:
            texto = str(cell).strip().lower()

            if texto.startswith(keyword.lower()):
                return i

    return -1


def parse_st(df, batch_id, data_upload):
    registros = []
    erros = []

    hr = find_header_row(df, "Planta")

    if hr < 0:
        erros.append("ST: coluna Planta não encontrada")
        return pd.DataFrame(), erros

    header = df.iloc[hr].tolist()

    pc = -1
    mc = -1
    rc = -1
    rlc = -1
    date_cols = []

    for j, value in enumerate(header):
        s = str(value).strip()
        sl = s.lower()

        if sl.startswith("planta"):
            pc = j
        elif s == "M300":
            mc = j
        elif s == "RF":
            rc = j
        elif sl == "real":
            rlc = j
        else:
            d = parse_date(value)

            if d:
                date_cols.append({"col": j, "date": d})

    if pc < 0 or not date_cols:
        erros.append("ST: estrutura inválida")
        return pd.DataFrame(), erros

    first_date = date_cols[0]["date"]
    ano = first_date.year
    mes = first_date.month

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
            valor = pv(row[dc["col"]])

            registros.append({
                "batch_id": batch_id,
                "fonte": "ST",
                "ano": ano,
                "mes": mes,
                "planta": planta,
                "kpi": "ST",
                "dia": data.day,
                "data_label": data.strftime("%d/%m"),
                "valor_real": valor,
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
        erros.append("FD: coluna Planta não encontrada")
        return pd.DataFrame(), erros

    header = df.iloc[hr].tolist()

    pc = -1
    kc = -1
    ac = -1
    date_cols = []

    for j, value in enumerate(header):
        s = str(value).strip()
        sl = s.lower()

        if sl.startswith("planta"):
            pc = j
        elif sl == "kpi":
            kc = j
        elif "real" in sl and "tt" in sl:
            ac = j
        else:
            d = parse_date(value)

            if d:
                date_cols.append({"col": j, "date": d})

    if pc < 0 or not date_cols:
        erros.append("FD: estrutura inválida")
        return pd.DataFrame(), erros

    first_date = date_cols[0]["date"]
    ano = first_date.year
    mes = first_date.month

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

        if "diário" in nome and "st" in nome:
            st_sheet = sheet

        if "diario" in nome and "st" in nome:
            st_sheet = sheet

        if "diário" in nome and "fd" in nome and "multiflex" in nome:
            fd_sheet = sheet

        if "diario" in nome and "fd" in nome and "multiflex" in nome:
            fd_sheet = sheet

    if st_sheet:
        arquivo.seek(0)

        df_st = pd.read_excel(
            arquivo,
            sheet_name=st_sheet,
            header=None,
            engine="openpyxl"
        )

        registros_st, erros_st = parse_st(df_st, batch_id, data_upload)

        if not registros_st.empty:
            todos.append(registros_st)

        erros.extend(erros_st)
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

        registros_fd, erros_fd = parse_fd(df_fd, batch_id, data_upload)

        if not registros_fd.empty:
            todos.append(registros_fd)

        erros.extend(erros_fd)
    else:
        erros.append("Aba 'Diário - FD Multiflex' não encontrada")

    if not todos:
        return pd.DataFrame(), erros

    df_final = pd.concat(todos, ignore_index=True)

    return df_final, erros


# ============================================================
# APP STREAMLIT
# ============================================================

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

            if df_records.empty:
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
