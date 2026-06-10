import pandas as pd

MAPA_RESULTADOS = {
    "COB": {
       ": "G143",        "Fornos": {
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
            "OEE": "K206",
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
    },
}


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
            "OEE": "K19",
            "FP": "G19",
            "FF": "E19",
            "MTBF": "I19",
            "%ST": "C34",
            "CT": "E34",
        },
        "Moagens Cru": {
            "OEE": "K144",
            "FP": "G144",
            "FF": "E144",
            "MTBF": "I144",
        },
        "Moagens Cimento": {
            "OEE": "K98",
            "FP": "G98",
            "FF": "E98",
            "MTBF": "I98",
            "%KKC": "F113",
        },
        "Ensacadeiras": {
            "OEE": "K264",
        },
        "Britagens": {
            "OEE": "K207",
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
    },

    "CUI": {
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
            "Argamassa": "D194",
        },
        "Volumes": {
            "Cimento": "C98",
            "Clínquer": "C19",
        },
    },

    "EDE": {
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
    },

    "NOB": {
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
            "OEE": "K264",
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
    },

    "PVE": {
        "Fornos": {
            "OEE": "K19",
            "FP": "G19",
            "FF": "E19",
            "MTBF": "I19",
            "%ST": None,
            "CT": None,
        },
        "Moagens Cru": {
            "OEE": None,
            "FP": None,
            "FF": None,
            "MTBF": None,
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
            "OEE": None,
        },
        "Estoques": {
            "Clínquer": "E41",
            "Granel": "D101",
            "Ensacado": "E101",
            "Argamassa": None,
        },
        "Volumes": {
            "Cimento": "C98",
            "Clínquer": None,
        },
    },

    "SOB": {
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
            "Argamassa": "D194",
        },
        "Volumes": {
            "Cimento": "C98",
            "Clínquer": "C19",
        },
    },

    "XAM": {
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
