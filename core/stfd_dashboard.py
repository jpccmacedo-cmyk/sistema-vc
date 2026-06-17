import pandas as pd


def cor_st(valor, m300, rf):
    if pd.isna(valor):
        return "background-color: #ffffff"

    tem_m300 = not pd.isna(m300)
    tem_rf = not pd.isna(rf)

    if tem_m300 and tem_rf:
        if valor >= m300 and valor >= rf:
            return "background-color: #C6EFCE"
        if valor < m300 and valor < rf:
            return "background-color: #FFC7CE"
        return "background-color: #FFEB9C"

    if tem_m300:
        return "background-color: #C6EFCE" if valor >= m300 else "background-color: #FFC7CE"

    if tem_rf:
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

    df_st["valor_real"] = pd.to_numeric(df_st["valor_real"], errors="coerce")
    df_st["m300"] = pd.to_numeric(df_st["m300"], errors="coerce")
    df_st["rf"] = pd.to_numeric(df_st["rf"], errors="coerce")
    df_st["acumulado_mes"] = pd.to_numeric(df_st["acumulado_mes"], errors="coerce")

    linhas = []

    for planta, bloco in df_st.groupby("planta"):
        bloco = bloco.sort_values("dia")

        m300 = bloco["m300"].dropna().iloc[0] if bloco["m300"].notna().any() else None
        rf = bloco["rf"].dropna().iloc[0] if bloco["rf"].notna().any() else None
        acc = bloco["acumulado_mes"].dropna().iloc[0] if bloco["acumulado_mes"].notna().any() else None

        linha = {
            "Planta": planta,
            "M300": m300,
            "RF": rf,
        }

        for _, row in bloco.iterrows():
            linha[row["data_label"]] = row["valor_real"]

        linha["Acc mês"] = acc

        linhas.append(linha)

    return pd.DataFrame(linhas)


def estilizar_st(tabela):
    if tabela.empty:
        return tabela

    colunas_dias = [
        c for c in tabela.columns
        if c not in ["Planta", "M300", "RF", "Acc mês"]
    ]

    def aplicar(row):
        estilos = []

        m300 = row.get("M300")
        rf = row.get("RF")

        for col in tabela.columns:
            if col in ["Planta", "M300", "RF"]:
                estilos.append("background-color: #eef2f7; font-weight: 600")
            elif col in colunas_dias:
                estilos.append(cor_st(row[col], m300, rf))
            elif col == "Acc mês":
                estilos.append(cor_st(row[col], m300, rf) + "; font-weight: 700")
            else:
                estilos.append("")

        return estilos

    return tabela.style.apply(aplicar, axis=1).format(precision=2)


def montar_tabela_fd(df_mes):
    df_fd = df_mes[df_mes["fonte"] == "FD"].copy()

    if df_fd.empty:
        return pd.DataFrame()

    df_fd["valor_real"] = pd.to_numeric(df_fd["valor_real"], errors="coerce")
    df_fd["acumulado_mes"] = pd.to_numeric(df_fd["acumulado_mes"], errors="coerce")

    linhas = []

    for planta, bloco in df_fd.groupby("planta"):
        bloco = bloco.sort_values("dia")

        acc = bloco["acumulado_mes"].dropna().iloc[0] if bloco["acumulado_mes"].notna().any() else None

        linha = {
            "Planta": planta,
        }

        for _, row in bloco.iterrows():
            linha[row["data_label"]] = row["valor_real"]

        linha["Real TT"] = acc

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

    format_dict = {}

    for col in tabela.columns:
        if col != "Planta":
            format_dict[col] = lambda x: "" if pd.isna(x) else f"{x:.2%}"

    return tabela.style.apply(aplicar, axis=1).format(format_dict)
