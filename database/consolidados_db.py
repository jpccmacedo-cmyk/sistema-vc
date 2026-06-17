from datetime import datetime
from io import BytesIO
import uuid
import json

import pandas("data_processada")import pandas as pd

    if data_processada:
        data_texto = data_processada.strftime("%Y-%m-%d")
        ano = data_processada.year
        mes = data_processada.month
    else:
        data_texto = None
        ano = None
        mes = None

    logs = json.dumps(resultado.get("logs", []), ensure_ascii=False)
    abas_criadas = json.dumps(resultado.get("abas_criadas", []), ensure_ascii=False)

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO consolidados_gerados (
                    consolidado_id,
                    nome_arquivo,
                    data_processada,
                    ano,
                    mes,
                    data_geracao,
                    arquivo_excel,
                    logs,
                    abas_criadas
                )
                VALUES (
                    :consolidado_id,
                    :nome_arquivo,
                    :data_processada,
                    :ano,
                    :mes,
                    :data_geracao,
                    :arquivo_excel,
                    :logs,
                    :abas_criadas
                )
            """),
            {
                "consolidado_id": consolidado_id,
                "nome_arquivo": nome_arquivo,
                "data_processada": data_texto,
                "ano": ano,
                "mes": mes,
                "data_geracao": data_geracao,
                "arquivo_excel": arquivo_bytes,
                "logs": logs,
                "abas_criadas": abas_criadas,
            }
        )

    wb = load_workbook(BytesIO(arquivo_bytes), data_only=True)
    df_indicadores = extrair_resultados_consolidado(wb)

    if not df_indicadores.empty:
        registros = []

        for _, row in df_indicadores.iterrows():
            registros.append({
                "id": str(uuid.uuid4()),
                "consolidado_id": consolidado_id,
                "data_processada": data_texto,
                "ano": ano,
                "mes": mes,
                "planta": row.get("Planta"),
                "grupo": row.get("Grupo"),
                "indicador": row.get("Indicador"),
                "celula": row.get("Celula"),
                "resultado": _normalizar_resultado_para_float(row.get("Resultado")),
                "data_geracao": data_geracao,
            })

        df_save = pd.DataFrame(registros)

        df_save.to_sql(
            "consolidado_indicadores",
            engine,
            if_exists="append",
            index=False
        )

    return consolidado_id


def salvar_resultados_consolidados_no_banco(resultados):
    ids = []

    for resultado in resultados:
        consolidado_id = salvar_consolidado_no_banco(resultado)
        ids.append(consolidado_id)

    return ids


def listar_consolidados():
    init_consolidados_db()

    engine = get_engine()

    query = """
        SELECT
            consolidado_id,
            nome_arquivo,
            data_processada,
            ano,
            mes,
            data_geracao,
            logs,
            abas_criadas
        FROM consolidados_gerados
        ORDER BY data_processada DESC, data_geracao DESC
    """

    return pd.read_sql(query, engine)


def carregar_indicadores_consolidados():
    init_consolidados_db()

    engine = get_engine()

    query = """
        SELECT
            i.*,
            c.nome_arquivo
        FROM consolidado_indicadores i
        LEFT JOIN consolidados_gerados c
            ON i.consolidado_id = c.consolidado_id
    """

    return pd.read_sql(query, engine)


def carregar_arquivo_consolidado(consolidado_id):
    init_consolidados_db()

    engine = get_engine()

    query = text("""
        SELECT
            nome_arquivo,
            arquivo_excel
        FROM consolidados_gerados
        WHERE consolidado_id = :consolidado_id
    """)

    with engine.begin() as conn:
        row = conn.execute(query, {"consolidado_id": consolidado_id}).fetchone()

    if not row:
        return None, None

    nome_arquivo = row[0]
    arquivo_excel = row[1]

    if isinstance(arquivo_excel, memoryview):
        arquivo_excel = arquivo_excel.tobytes()

    return nome_arquivo, arquivo_excel


def excluir_consolidado(consolidado_id):
    init_consolidados_db()

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM consolidado_indicadores WHERE consolidado_id = :consolidado_id"),
            {"consolidado_id": consolidado_id}
        )

        conn.execute(
            text("DELETE FROM consolidados_gerados WHERE consolidado_id = :consolidado_id"),
            {"consolidado_id": consolidado_id}
        )
from sqlalchemy import text
from openpyxl import load_workbook

from database.connection import get_engine
from utils.mapa_indicadores import extrair_resultados_consolidado


def init_consolidados_db():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS consolidados_gerados (
                consolidado_id TEXT PRIMARY KEY,
                nome_arquivo TEXT NOT NULL,
                data_processada TEXT,
                ano INTEGER,
                mes INTEGER,
                data_geracao TEXT NOT NULL,
                arquivo_excel BYTEA,
                logs TEXT,
                abas_criadas TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS consolidado_indicadores (
                id TEXT PRIMARY KEY,
                consolidado_id TEXT NOT NULL,
                data_processada TEXT,
                ano INTEGER,
                mes INTEGER,
                planta TEXT,
                grupo TEXT,
                indicador TEXT,
                celula TEXT,
                resultado REAL,
                data_geracao TEXT NOT NULL
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_consolidado_indicadores_filtros
            ON consolidado_indicadores (ano, mes, planta, grupo, indicador)
        """))


def _bytes_from_resultado(resultado):
    arquivo_excel = resultado["arquivo_excel"]
    arquivo_excel.seek(0)
    return arquivo_excel.getvalue()


def _normalizar_resultado_para_float(valor):
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
        texto = valor.strip().replace("%", "").replace(".", "").replace(",", ".")

        if texto in ["", "-", "NÃO TEM", "NAO TEM", "N/A"]:
            return None

        try:
            return float(texto)
        except Exception:
            return None

    return None


def salvar_consolidado_no_banco(resultado):
    init_consolidados_db()

    consolidado_id = str(uuid.uuid4())
    data_geracao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    nome_arquivo = resultado["nome_arquivo_final"]
    arquivo_bytes = _bytes_from_resultado(resultado)

