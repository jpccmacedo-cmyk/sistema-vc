from datetime import datetime, date
from io import BytesIO

import pandas as pd


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

        if "diário" in nome and "fd" in nome and "multiflex" in nome:
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
``
