import pandas as pd


def base_padrao():
    return {
        "Fornos": {
            "OEE": "K19",
            "FP": "G19",
            "FF": "E19",
            "MTBF": "I19",
            "%ST": "C34",
            "CT": "E34",
        },
        "Moagens Cru": {
            "OEE": "K143",
            "FP": "G143",
            "FF": "E143",
            "MTBF": "I143",
        },
        "Moagens Cimento": {
            "OEE": "K98",
            "FP": "G98",
            "FF": "E98",
            "MTBF": "I98",
            "%KKC": "F112",
        },
        "Ensacadeiras": {
            "OEE": "K263",
        },
        "Britagens": {
            "OEE": "K215",
        },
        "Estoques": {
            "Clínquer": "E41",
            "Granel": "D101",
            "Ensacado": "E101",
            "Argamassa": None,
        },
        "Volumes": {
            "Cimento": "C98",
            "Clínquer": "C19",
        },
    }


MAPA_RESULTADOS = {
    "COB": base_padrao(),
    "CUI": base_padrao(),
    "EDE": base_padrao(),
    "NOB": base_padrao(),
    "PVE": base_padrao(),
    "SOB": base_padrao(),
    "XAM": base_padrao(),
}

# Ajustes específicos por planta

MAPA_RESULTADOS["COB"]["Moagens Cru"] = {
    "OEE": "K144",
    "FP": "G144",
    "FF": "E144",
    "MTBF": "I144",
}
MAPA_RESULTADOS["COB"]["Moagens Cimento"]["%KKC"] = "F113"
MAPA_RESULTADOS["COB"]["Ensacadeiras"]["OEE"] = "K264"
MAPA_RESULTADOS["COB"]["Britagens"]["OEE"] = "K207"
MAPA_RESULTADOS["COB"]["Estoques"]["Argamassa"] = None

MAPA_RESULTADOS["CUI"]["Estoques"]["Argamassa"] = "D194"

MAPA_RESULTADOS["NOB"]["Ensacadeiras"]["OEE"] = "K264"

MAPA_RESULTADOS["PVE"]["Fornos"]["%ST"] = None
MAPA_RESULTADOS["PVE"]["Fornos"]["CT"] = None
MAPA_RESULTADOS["PVE"]["Moagens Cru"] = {
    "OEE": None,
    "FP": None,
    "FF": None,
    "MTBF": None,
}
MAPA_RESULTADOS["PVE"]["Britagens"]["OEE"] = None
MAPA_RESULTADOS["PVE"]["Volumes"]["Clínquer"] = None

MAPA_RESULTADOS["SOB"]["Estoques"]["Argamassa"] = "D194"

MAPA_RESULTADOS["XAM"]["Britagens"]["OEE"] = "K206"


def normalizar_valor(valor):
    if valor is None:
        return None

    if isinstance(valor, str):
        texto = valor.strip()

        if texto.upper() in ["", "-", "NÃO TEM", "NAO TEM", "N/A"]:
            return None

        texto_num = texto.replace("%", "").replace(".", "").replace(",", ".")

        try:
            return float(texto_num)
        except Exception:
            return valor

    return valor


def extrair_resultados_consolidado(wb):
    registros = []

    for planta, grupos in MAPA_RESULTADOS.items():
        if planta not in wb.sheetnames:
            continue

        ws = wb[planta]

        for grupo, indicadores in grupos.items():
            for indicador, celula in indicadores.items():
                valor = None if celula is None else ws[celula].value

                registros.append({
                    "Planta": planta,
                    "Grupo": grupo,
                    "Indicador": indicador,
                    "Celula": celula,
                    "Resultado": normalizar_valor(valor),
                })

    return pd.DataFrame(registros)
